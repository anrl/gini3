/**
 * openflow_ctrl_iface.c - OpenFlow controller interface
 *
 * Author: Michael Kourlas
 * Date: November 26, 2015
 */

#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <pthread.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>

#include "message.h"
#include "openflow.h"
#include "openflow_config.h"

#include "openflow_ctrl_iface.h"

// Controller socket file descriptor
static int32_t ofc_socket_fd;
pthread_mutex_t ofc_socket_mutex;

// Transaction ID counter
static uint32_t txid = 0;

// Connection status
static uint8_t connection_status;
pthread_mutex_t connection_status_mutex;

/**
 * Gets a transaction ID. This transaction ID will not have been used to send
 * data from the switch before unless more than 2^32 messages have been sent.
 *
 * @return A transaction ID that probably has not been used to send data from
 *         the switch before.
 */
static uint32_t openflow_ctrl_iface_get_txid()
{
	return txid++;
}

/**
 * Gets the current controller connection state.
 *
 * @return The current controller connection state.
 */
uint8_t openflow_ctrl_iface_up() {
	pthread_mutex_lock(&connection_status_mutex);
	return connection_status;
	pthread_mutex_unlock(&connection_status_mutex);
}

/**
 * Sets the current controller connection state to up.
 */
static void openflow_ctrl_iface_conn_up()
{
	pthread_mutex_lock(&connection_status_mutex);
	connection_status = 1;
	pthread_mutex_unlock(&connection_status_mutex);
}

/**
 * Sets the current controller connection state to down.
 */
static void openflow_ctrl_iface_conn_down()
{
	pthread_mutex_lock(&connection_status_mutex);
	connection_status = 0;
	pthread_mutex_unlock(&connection_status_mutex);
}

/**
 * Gets a template for an OpenFlow error message. The message is created using
 * dynamically-allocated memory and must be freed when no longer needed.
 *
 * @return A pointer to an OpenFlow error message template.
 */
static ofp_error_msg* openflow_ctrl_iface_create_error_msg()
{
	// Prepare error message
	ofp_error_msg* error_msg = malloc(sizeof(ofp_error_msg));
	error_msg->header.version = OFP_VERSION;
	error_msg->header.type = OFPT_ERROR;
	error_msg->header.length = htons(OPENFLOW_ERROR_MSG_SIZE);

	return error_msg;
}

/**
 * Sends an OpenFlow message to the controller TCP socket.
 *
 * @param data A pointer to the message.
 * @param len  The length of the message in bytes.
 *
 * @return The number of bytes sent, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_send(void *data, uint32_t len)
{
	uint8_t counter = 0;
	uint32_t sent = 0;
	verbose(2, "[openflow_ctrl_iface_send]:: Sending message to controller.");
	while (sent < len && counter < 10)
	{
		pthread_mutex_lock(&ofc_socket_mutex);
		int32_t ret = send(ofc_socket_fd, data + sent, len - sent, 0);
		pthread_mutex_unlock(&ofc_socket_mutex);

		if (ret < 0)
		{
			verbose(2, "[openflow_ctrl_iface_send]:: Unknown error occurred.");
			return OPENFLOW_CTRL_IFACE_ERR_UNKNOWN;
		}
		else if (ret == 0)
		{
			counter += 1;
			sleep(1);
		}
		else if (ret < len - sent)
		{
			sent += ret;
			sleep(1);
		}
		sent += ret;
	}

	if (sent < len)
	{
		verbose(2, "[openflow_ctrl_iface_send]:: Send timeout reached.");
		return OPENFLOW_CTRL_IFACE_SEND_TIMEOUT;
	}

	verbose(2, "[openflow_ctrl_iface_send]:: Message sent to controller.");
	return sent;
}

/**
 * Gets the next OpenFlow message from the controller TCP socket. The message
 * is created using dynamically-allocated memory and must be freed when no
 * longer needed.
 *
 * @param A pointer to a void pointer. The void pointer will be replaced with a
 *        pointer to the message if one is received.
 *
 * @return The number of bytes in the message, 0 if no message was received,
 *         or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_recv(void **ptr_to_msg)
{
	ofp_header header;
	pthread_mutex_lock(&ofc_socket_mutex);
	int32_t ret = recv(ofc_socket_fd, &header, sizeof(header), MSG_DONTWAIT);
	pthread_mutex_unlock(&ofc_socket_mutex);
	if (ret == 0) {
		verbose(2, "[openflow_ctrl_iface_recv]:: Controller connection"
			" closed.");
		return OPENFLOW_CTRL_IFACE_ERR_CONN_CLOSED;
	}
	else if (ret == -1)
	{
		if (errno == EAGAIN)
		{
			return 0;
		}
		else
		{
			verbose(2, "[openflow_ctrl_iface_recv]:: Unknown error.");
			return OPENFLOW_CTRL_IFACE_ERR_UNKNOWN;
		}
	}

	verbose(2, "[openflow_ctrl_iface_recv]:: Message received from"
		" controller.");
	if (header.version != OFP_VERSION)
	{
		verbose(2, "[openflow_ctrl_iface_recv]:: Bad OpenFlow version number.");

		ofp_error_msg* error_msg = openflow_ctrl_iface_create_error_msg();
		error_msg->header.xid = header.xid;
		error_msg->type = htons(OFPET_BAD_REQUEST);
		error_msg->code = htons(OFPBRC_BAD_VERSION);

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		if (ret < 0)
		{
			return ret;
		}
		return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
	}
	else if (header.type > OFPT_QUEUE_GET_CONFIG_REPLY)
	{
		verbose(2, "[openflow_ctrl_iface_recv]:: Unsupported message type.");
		ofp_error_msg* error_msg = openflow_ctrl_iface_create_error_msg();
		error_msg->header.xid = header.xid;
		error_msg->type = htons(OFPET_BAD_REQUEST);
		error_msg->code = htons(OFPBRC_BAD_TYPE);

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		if (ret < 0)
		{
			return ret;
		}
		return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
	}

	void *msg = malloc(header.length);
	memcpy(msg, &header, sizeof(header));

	pthread_mutex_lock(&ofc_socket_mutex);
	ret = recv(ofc_socket_fd, msg + sizeof(header),
		header.length - sizeof(header), 0);
	pthread_mutex_unlock(&ofc_socket_mutex);
	if (ret == 0) {
		verbose(2, "[openflow_ctrl_iface_recv]:: Controller connection"
			" closed.");
		return OPENFLOW_CTRL_IFACE_ERR_CONN_CLOSED;
	}
	else if (ret == -1)
	{
		if (errno == EAGAIN)
		{
			return 0;
		}
		else
		{
			verbose(2, "[openflow_ctrl_iface_recv]:: Unknown error.");
			return OPENFLOW_CTRL_IFACE_ERR_UNKNOWN;
		}
	}

	verbose(2, "[openflow_ctrl_iface_recv]:: Message successfully processed.");
	*ptr_to_msg = msg;
	return header.length;
}

/**
 * Sends a hello message to the OpenFLow controller.
 *
 * @return The number of bytes sent, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_send_hello()
{
    verbose(2, "[openflow_ctrl_iface_send_hello]:: Preparing hello message.");

	ofp_hello hello_request;
	hello_request.header.version = OFP_VERSION;
	hello_request.header.type = OFPT_HELLO;
	hello_request.header.length = htons(8);
	hello_request.header.xid = htonl(openflow_ctrl_iface_get_txid());
	return openflow_ctrl_iface_send(&hello_request, sizeof(hello_request));
}

/**
 * Processes a hello message from the OpenFLow controller.
 *
 * @return 0, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_recv_hello(ofp_hello* hello)
{
	ofp_error_msg* error_msg = openflow_ctrl_iface_create_error_msg();
	error_msg->header.xid = hello->header.xid;
	error_msg->type = OFPET_HELLO_FAILED;

	if (hello->header.version < OFP_VERSION ||
		hello->header.type != OFPT_HELLO ||
		ntohs(hello->header.length) != 8)
	{
		verbose(2, "[openflow_ctrl_iface_recv_hello]:: Incompatible"
			" OpenFlow controller version.");
		error_msg->code = OFPHFC_INCOMPATIBLE;

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		if (ret < 0)
		{
			return ret;
		}
		return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
	}

	verbose(2, "[openflow_ctrl_iface_recv_hello]:: OpenFlow controller"
		" hello message valid.");
	return 0;
}

/**
 * Performs the initial OpenFLow controller connection setup (the hello
 * request/reply mechanism).
 *
 * @return 0, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_hello_req_rep()
{
	verbose(2, "[openflow_ctrl_iface_hello_req_rep]:: Performing controller"
		" hello request/reply.");
	int32_t ret = openflow_ctrl_iface_send_hello();
	if (ret < 0)
	{
		return ret;
	}

	ofp_hello* hello;
	do
	{
		ret = openflow_ctrl_iface_recv((void **)&hello);
	}
	while (ret == 0);
	if (ret < 0)
	{
		return ret;
	}

	return openflow_ctrl_iface_recv_hello(hello);
}

/**
 * Processes a features request message from the OpenFLow controller.
 *
 * @return 0, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_recv_features_req(
    ofp_header* features_request)
{
    ofp_error_msg* error_msg = openflow_ctrl_iface_create_error_msg();
    error_msg->header.xid = features_request->xid;
    error_msg->type = OFPET_BAD_REQUEST;

    if (features_request->type != OFPT_FEATURES_REQUEST)
    {
        verbose(2, "[openflow_ctrl_iface_recv_features_req]:: Unexpected"
            " message type.");
        error_msg->code = OFPBRC_BAD_TYPE;

        int32_t ret = openflow_ctrl_iface_send(error_msg,
            OPENFLOW_ERROR_MSG_SIZE);
        if (ret < 0)
        {
            return ret;
        }
        return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
    }
    if (ntohs(features_request->length) != 8)
    {
        verbose(2, "[openflow_ctrl_iface_recv_features_req]:: Unexpected"
            " message length.");
        error_msg->code = OFPBRC_BAD_LEN;

        int32_t ret = openflow_ctrl_iface_send(error_msg,
            OPENFLOW_ERROR_MSG_SIZE);
        if (ret < 0)
        {
            return ret;
        }
        return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
    }

    verbose(2, "[openflow_ctrl_iface_recv_features_req]:: OpenFlow controller"
        " features request message valid.");
    return 0;
}

/**
 * Sends a features reply message to the OpenFLow controller.
 *
 * @return The number of bytes sent, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_send_features_rep()
{
    verbose(2, "[openflow_ctrl_iface_send_features_rep]:: Preparing features"
        " reply message.");

    ofp_switch_features switch_features;
    ofp_phy_port phy_ports[OPENFLOW_MAX_PHYSICAL_PORTS];

    void *features_reply = malloc(sizeof(switch_features) + sizeof(phy_ports));
    memcpy(features_reply, &switch_features, sizeof(switch_features));
    memcpy(features_reply + sizeof(switch_features), phy_ports,
        sizeof(phy_ports));
    int32_t ret = openflow_ctrl_iface_send(features_reply,
        sizeof(switch_features) + sizeof(phy_ports));
    if (ret < 0)
    {
        return ret;
    }
    return 0;
}

/**
 * Performs the initial OpenFlow features request/reply.
 *
 * @return 0, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_features_req_rep()
{
	verbose(2, "[openflow_ctrl_iface_features_req_rep]:: Performing controller"
		" features request/reply.");
	ofp_header* features_request;
    int32_t ret;
	do
	{
		ret = openflow_ctrl_iface_recv((void **)&features_request);
	}
	while (ret == 0);
	if (ret < 0)
	{
		return ret;
	}

	ret = openflow_ctrl_iface_recv_features_req(features_request);
	if (ret < 0)
	{
		return ret;
	}

	return openflow_ctrl_iface_send_features_rep();
}

/**
 * OpenFlow controller thread.
 *
 * @param pn Pointer to the controller TCP port number.
 */
void *openflow_ctrl_iface(void *pn)
{
	int32_t *port_num = (int32_t *)pn;
	if (*port_num < 1 || *port_num > 65535)
	{
		fatal("[openflow_ctrl_iface]:: Invalid port number"
			" %d.", *port_num);
		exit(1);
	}

	verbose(1, "[openflow_ctrl_iface]:: Connecting to controller.");

	struct sockaddr_in ofc_sock_addr;
	ofc_sock_addr.sin_family = AF_INET;
	ofc_sock_addr.sin_port = htons(*port_num);
	inet_aton("127.0.0.1", &ofc_sock_addr.sin_addr);

	pthread_mutex_lock(&ofc_socket_mutex);
	ofc_socket_fd = socket(AF_INET, SOCK_STREAM, 0);
	int32_t status = connect(ofc_socket_fd, (struct sockaddr*)&ofc_sock_addr,
		sizeof(ofc_sock_addr));
	if (status != 0)
	{
		fatal("[openflow_ctrl_iface]:: Failed to connect to controller"
			" socket.");
		exit(1);
	}
	pthread_mutex_unlock(&ofc_socket_mutex);

	openflow_ctrl_iface_hello_req_rep();
	// openflow_ctrl_iface_features_req_rep();

	openflow_ctrl_iface_conn_up();

	while (1)
	{
		// Receive data and pass to controller
		pthread_mutex_lock(&ofc_socket_mutex);
		// TODO: Implement this
		pthread_mutex_unlock(&ofc_socket_mutex);
		sleep(1);
	}

	free(pn);
}

pthread_t openflow_ctrl_iface_init(int32_t port_num)
{
	int32_t threadstat;
	pthread_t threadid;

	int32_t *pn = malloc(sizeof(int));
	*pn = port_num;
	threadstat = pthread_create((pthread_t *)&threadid, NULL,
		(void *)openflow_ctrl_iface, pn);
	return threadid;
}


void openflow_ctrl_iface_send_to_ctrl(gpacket_t *packet)
{
	pthread_mutex_lock(&ofc_socket_mutex);
	// TODO: Implement this function
	pthread_mutex_unlock(&ofc_socket_mutex);

}

void openflow_ctrl_iface_parse_packet(gpacket_t *packet)
{
	// TODO: Implement this function
}
