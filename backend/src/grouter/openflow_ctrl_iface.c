/**
 * openflow_ctrl_iface.c - OpenFlow controller interface
 */

#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <pthread.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>

#include "gnet.h"
#include "message.h"
#include "ip.h"
#include "openflow.h"
#include "openflow_config.h"
#include "openflow_flowtable.h"
#include "protocols.h"
#include "tcp.h"

#include "openflow_ctrl_iface.h"

// Controller socket file descriptor
static int32_t ofc_socket_fd;
pthread_mutex_t ofc_socket_mutex;

// Transaction ID counter
static uint32_t txid = 0;

// Connection status
static uint8_t connection_status = 0;
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
uint8_t openflow_ctrl_iface_get_conn_state() {
	pthread_mutex_lock(&connection_status_mutex);
	uint8_t status = connection_status;
	pthread_mutex_unlock(&connection_status_mutex);
	return status;
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

	// TODO: Delete all non-emergency entries in flowtable.
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
	ofp_error_msg* error_msg = malloc(sizeof(ofp_error_msg) + 64);
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

	verbose(2, "[openflow_ctrl_iface_recv]:: Header of message received from"
		" controller.");
	if (header.version != OFP_VERSION)
	{
		verbose(2, "[openflow_ctrl_iface_recv]:: Bad OpenFlow version number.");

		ofp_error_msg* error_msg = openflow_ctrl_iface_create_error_msg();
		error_msg->header.xid = header.xid;
		error_msg->type = htons(OFPET_BAD_REQUEST);
		error_msg->code = htons(OFPBRC_BAD_VERSION);
		memcpy(&error_msg->data, &header, sizeof(ofp_header));

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		free(error_msg);
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
		memcpy(&error_msg->data, &header, sizeof(ofp_header));

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		free(error_msg);
		if (ret < 0)
		{
			return ret;
		}
		return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
	}

	void *msg = malloc(ntohs(header.length));
	memcpy(msg, &header, sizeof(header));

	if (ntohs(header.length) - sizeof(header) > 0)
	{
		pthread_mutex_lock(&ofc_socket_mutex);
		ret = recv(ofc_socket_fd, msg + sizeof(header),
			ntohs(header.length) - sizeof(header), 0);
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
	}

	verbose(2, "[openflow_ctrl_iface_recv]:: Message received from"
		" controller.");
	*ptr_to_msg = msg;
	return ntohs(header.length);
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
	if (hello->header.version < OFP_VERSION ||
		hello->header.type != OFPT_HELLO ||
		ntohs(hello->header.length) != 8)
	{
		verbose(2, "[openflow_ctrl_iface_recv_hello]:: Incompatible"
			" OpenFlow controller version.");

		ofp_error_msg* error_msg = openflow_ctrl_iface_create_error_msg();
		error_msg->header.xid = hello->header.xid;
		error_msg->type = ntohs(OFPET_HELLO_FAILED);
		error_msg->code = ntohs(OFPHFC_INCOMPATIBLE);
		memcpy(&error_msg->data, hello, sizeof(ofp_hello));

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		free(error_msg);
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

	ret = openflow_ctrl_iface_recv_hello(hello);
	free(hello);
	return ret;
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
	error_msg->type = ntohs(OFPET_BAD_REQUEST);

	if (features_request->type != OFPT_FEATURES_REQUEST)
	{
		verbose(2, "[openflow_ctrl_iface_recv_features_req]:: Unexpected"
			" message type.");
		error_msg->code = ntohs(OFPBRC_BAD_TYPE);
		memcpy(&error_msg->data, features_request, sizeof(ofp_header));

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		free(error_msg);
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
		error_msg->code = ntohs(OFPBRC_BAD_LEN);
		memcpy(&error_msg->data, features_request, sizeof(ofp_header));

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		free(error_msg);
		if (ret < 0)
		{
			return ret;
		}
		return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
	}

	free(error_msg);
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
	uint32_t i;
	verbose(2, "[openflow_ctrl_iface_send_features_rep]:: Preparing features"
		" reply message.");

	ofp_switch_features switch_features = openflow_config_get_switch_features();
	ofp_phy_port *phy_ports[OPENFLOW_MAX_PHYSICAL_PORTS];

	switch_features.header.version = OFP_VERSION;
	switch_features.header.type = OFPT_FEATURES_REPLY;
	switch_features.header.length = htons(sizeof(switch_features) +
		(OPENFLOW_MAX_PHYSICAL_PORTS * sizeof(ofp_phy_port)));
	switch_features.header.xid = htonl(openflow_ctrl_iface_get_txid());

	for (i = 0; i < OPENFLOW_MAX_PHYSICAL_PORTS; i++)
	{
		phy_ports[i] = openflow_config_get_phy_port(
			openflow_config_gnet_to_of_port_num(i));
	}

	void *features_reply = malloc(sizeof(switch_features) +
		(OPENFLOW_MAX_PHYSICAL_PORTS * sizeof(ofp_phy_port)));
	memcpy(features_reply, &switch_features, sizeof(switch_features));
	for (i = 0; i < OPENFLOW_MAX_PHYSICAL_PORTS; i++)
	{
		memcpy(features_reply + sizeof(switch_features) +
			(i * sizeof(ofp_phy_port)), phy_ports[i], sizeof(ofp_phy_port));
	}
	int32_t ret = openflow_ctrl_iface_send(features_reply,
		sizeof(switch_features) +
		(OPENFLOW_MAX_PHYSICAL_PORTS * sizeof(ofp_phy_port)));
	free(features_reply);
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
	ofp_header *features_request;
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
	free(features_request);
	if (ret < 0)
	{
		return ret;
	}

	return openflow_ctrl_iface_send_features_rep();
}

/**
 * Processes a set config message from the OpenFLow controller.
 *
 * @return 0, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_recv_set_config(
	ofp_switch_config *switch_config)
{
	if (ntohs(switch_config->header.length) != 12)
	{
		verbose(2, "[openflow_ctrl_iface_recv_set_config]:: Unexpected"
			" message length.");

		ofp_error_msg* error_msg = openflow_ctrl_iface_create_error_msg();
		error_msg->header.xid = switch_config->header.xid;
		error_msg->type = htons(OFPET_BAD_REQUEST);
		error_msg->code = htons(OFPBRC_BAD_LEN);
		memcpy(&error_msg->data, switch_config, sizeof(ofp_switch_config));

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		free(error_msg);
		if (ret < 0)
		{
			return ret;
		}
		return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
	}

	verbose(2, "[openflow_ctrl_iface_recv_features_req]:: OpenFlow controller"
		" set config message valid.");

	openflow_config_set_switch_config_flags(switch_config->flags);
	openflow_config_set_miss_send_len(switch_config->miss_send_len);

	return 0;
}

/**
 * Processes a barrier request message from the OpenFLow controller.
 *
 * @return 0, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_recv_barrier_req(
	ofp_header *barrier_request)
{
	if (ntohs(barrier_request->length) != 8)
	{
		verbose(2, "[openflow_ctrl_iface_recv_barrier_req]:: Unexpected"
			" message length.");

		ofp_error_msg* error_msg = openflow_ctrl_iface_create_error_msg();
		error_msg->header.xid = barrier_request->xid;
		error_msg->type = htons(OFPET_BAD_REQUEST);
		error_msg->code = htons(OFPBRC_BAD_LEN);
		memcpy(&error_msg->data, barrier_request, sizeof(ofp_header));

		int32_t ret = openflow_ctrl_iface_send(error_msg,
			OPENFLOW_ERROR_MSG_SIZE);
		free(error_msg);
		if (ret < 0)
		{
			return ret;
		}
		return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
	}

	verbose(2, "[openflow_ctrl_iface_recv_barrier_req]:: OpenFlow controller"
		" barrier request message valid.");

	return 0;
}

/**
 * Sends a barrier reply message to the OpenFLow controller.
 *
 * @return The number of bytes sent, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_send_barrier_rep(uint32_t txid)
{
	verbose(2, "[openflow_ctrl_iface_send_barrier_rep]:: Preparing barrier"
		" reply message.");

	ofp_header barrier_response;
	barrier_response.version = OFP_VERSION;
	barrier_response.type = OFPT_BARRIER_REPLY;
	barrier_response.length = htons(8);
	barrier_response.xid = txid;

	return openflow_ctrl_iface_send(&barrier_response,
		sizeof(barrier_response));
}

/**
 * Processes a flow mod message from the OpenFLow controller.
 *
 * @return 0, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_recv_flow_mod(ofp_flow_mod *flow_mod)
{
	ofp_error_msg* error_msg = openflow_ctrl_iface_create_error_msg();
	error_msg->header.xid = flow_mod->header.xid;
	error_msg->type = htons(OFPET_FLOW_MOD_FAILED);

	int32_t ret;
	if (ntohs(flow_mod->header.length) < 72)
	{
		verbose(2, "[openflow_ctrl_iface_recv_flow_mod]:: Unexpected"
			" message length.");

		error_msg->type = htons(OFPET_BAD_REQUEST);
		error_msg->code = htons(OFPBRC_BAD_LEN);
		memcpy(&error_msg->data, flow_mod, 64);

		ret = openflow_ctrl_iface_send(error_msg, OPENFLOW_ERROR_MSG_SIZE);
		free(error_msg);
		if (ret < 0)
		{
			return ret;
		}
		return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
	}

	ret = openflow_flowtable_modify(flow_mod, error_msg);
	if (ret < 0)
	{
		memcpy(&error_msg->data, flow_mod, 64);
		ret = openflow_ctrl_iface_send(error_msg, OPENFLOW_ERROR_MSG_SIZE);
		free(error_msg);
		if (ret < 0)
		{
			return ret;
		}
		return OPENFLOW_CTRL_IFACE_ERR_OPENFLOW;
	}

	verbose(2, "[openflow_ctrl_iface_recv_flow_mod]:: OpenFlow controller"
		" flow mod message valid.");

	free(error_msg);
	return 0;
}

static int32_t openflow_ctrl_iface_send_echo_rep()
{
	// TODO: Implement this.
}

static int32_t openflow_ctrl_iface_send_config_rep()
{
	// TODO: Implement this.
}

int32_t openflow_ctrl_iface_send_packet_in(gpacket_t *packet)
{
	// TODO: Implement this.
}

int32_t openflow_ctrl_iface_send_flow_removed(
		openflow_flowtable_entry_type *entry, uint8_t reason)
{
	// TODO: Implement this.
}

int32_t openflow_ctrl_iface_send_port_status(ofp_phy_port *phy_port)
{
	// TODO: Implement this.
}

static int32_t openflow_ctrl_iface_send_stats_reply()
{
	// TODO: Implement this.
}

/**
 * Parses a message from the OpenFlow controller.
 *
 * @param message The message to parse.
 *
 * @return 0, or a negative value if an error occurred.
 */
static int32_t openflow_ctrl_iface_parse_message(ofp_header *message)
{
	int32_t ret;
	switch(message->type)
	{
		case OFPT_ECHO_REQUEST:
		{
			// TODO: Implement this.
			break;
		}
		case OFPT_SET_CONFIG:
		{
			ofp_switch_config *switch_config = (ofp_switch_config *)message;
			ret = openflow_ctrl_iface_recv_set_config(switch_config);
			break;
		}
		case OFPT_GET_CONFIG_REQUEST:
		{
			// TODO: Implement this.
			break;
		}
		case OFPT_PACKET_OUT:
		{
			// TODO: Implement this.
			break;
		}
		case OFPT_FLOW_MOD:
		{
			ofp_flow_mod *flow_mod = (ofp_flow_mod *)message;
			ret = openflow_ctrl_iface_recv_flow_mod(flow_mod);
			break;
		}
		case OFPT_PORT_MOD:
		{
			// TODO: Implement this.
			break;
		}
		case OFPT_STATS_REQUEST:
		{
			// TODO: Implement this.
			break;
		}
		case OFPT_BARRIER_REQUEST:
		{
			ofp_header *barrier_request = message;
			ret = openflow_ctrl_iface_recv_barrier_req(barrier_request);
			if (ret < 0)
			{
				return ret;
			}
			ret = openflow_ctrl_iface_send_barrier_rep(barrier_request->xid);
			break;
		}
		default:
		{
			break;
		}
	}

	if (ret < 0) {
		return ret;
	}
	return 0;
}

/**
 * Parses a packet as though it came from the OpenFlow controller.
 *
 * @param packet The packet to parse.
 */
void openflow_ctrl_iface_parse_packet(gpacket_t *packet)
{
	if (ntohs(packet->data.header.prot) == IP_PROTOCOL)
	{
		ip_packet_t *ip_packet = (ip_packet_t *) &packet->data.data;
		if (!(ntohs(ip_packet->ip_frag_off) & 0x1fff) &&
			!(ntohs(ip_packet->ip_frag_off) & 0x2000))
		{
			if (ip_packet->ip_prot == TCP_PROTOCOL)
			{
				uint32_t ip_header_length = ip_packet->ip_hdr_len * 4;
				tcp_packet_type *tcp_packet = (tcp_packet_type *)
					((uint8_t *) ip_packet + ip_header_length);

				ofp_header *message = (ofp_header *) (tcp_packet +
					sizeof(tcp_packet_type));
				openflow_ctrl_iface_parse_message(message);
			}
		}
	}
}

/**
 * OpenFlow controller thread. Connects to controller and passes incoming
 * packets to handlers.
 *
 * @param pn Pointer to the controller TCP port number.
 */
void openflow_ctrl_iface(void *pn)
{
	while (1)
	{
		int32_t *port_num = (int32_t *)pn;
		if (*port_num < 1 || *port_num > 65535)
		{
			fatal("[openflow_ctrl_iface]:: Invalid controller TCP port number"
				" %d.", *port_num);
			exit(1);
		}

		verbose(2, "[openflow_ctrl_iface]:: Sleeping for 15 seconds to allow"
			" interfaces to be configured before connecting to controller.");
		sleep(15);

		openflow_config_set_phy_port_defaults();

		verbose(2, "[openflow_ctrl_iface]:: Connecting to controller.");

		struct sockaddr_in ofc_sock_addr;
		ofc_sock_addr.sin_family = AF_INET;
		ofc_sock_addr.sin_port = htons(*port_num);
		inet_aton("127.0.0.1", &ofc_sock_addr.sin_addr);

		pthread_mutex_lock(&ofc_socket_mutex);
		ofc_socket_fd = socket(AF_INET, SOCK_STREAM, 0);
		int32_t status = connect(ofc_socket_fd,
			(struct sockaddr*)&ofc_sock_addr, sizeof(ofc_sock_addr));
		if (status != 0)
		{
			fatal("[openflow_ctrl_iface]:: Failed to connect to controller"
				" socket.");
			exit(1);
		}
		pthread_mutex_unlock(&ofc_socket_mutex);

		verbose(2, "[openflow_ctrl_iface]:: Connected to controller. Starting"
			" connection setup.");

		openflow_ctrl_iface_hello_req_rep();
		openflow_ctrl_iface_features_req_rep();
		openflow_ctrl_iface_conn_up();

		verbose(2, "[openflow_ctrl_iface]:: Connection setup complete. Now"
			" receiving messages.");

		while (1)
		{
			// Receive a message from controller
			ofp_header *message = NULL;
			int32_t ret;
			do
			{
				ret = openflow_ctrl_iface_recv((void **)&message);
				if (ret == 0)
				{
					sleep(1);
				}
			}
			while (ret == 0);

			if (message == NULL)
			{
				// Controller connection lost
				openflow_ctrl_iface_conn_down();
				break;
			}
			else
			{
				// Process received message
				openflow_ctrl_iface_parse_message(message);
				free(message);
			}
		}
	}

	free(pn);
}

/**
 * Initializes the OpenFlow controller-switch interface.
 *
 * @param port_num The TCP port number of the OpenFlow controller.
 *
 * @return The thread associated with the controller interface.
 */
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
