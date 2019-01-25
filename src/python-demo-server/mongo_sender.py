import datetime
import logging

from pymongo import monitoring


class Metric:
    def __init__(self, name, value, attributes={}):
        assert '_id' not in attributes, 'attributes must not have _id'

        props = []

        for k in attributes:
            props.append(k + '="' + attributes[k] + '"')

        self.props = props
        self.name = str(name)
        self.value = str(value)
        self.id = None

    def set_value(self, value):
        self.value = str(value)


class MetricList:
    def __init__(self, metrics, instanceInfo):
        assert 'name' not in instanceInfo, 'instanceInfo should not have key "name"'
        assert 'value' not in instanceInfo, 'instanceInfo should not have key "value"'

        self.instanceInfo = instanceInfo
        inst_props = []
        inst_props_string = ''
        for k in instanceInfo:
            inst_props.append(k + '="' + instanceInfo[k] + '"')

        if len(inst_props) != 0:
            inst_props_string += ",".join(inst_props) + ","

        self.inst_props_string = inst_props_string
        self.metrics = metrics

    def update(self, col):
        # lines = []
        import pymongo
        for info in self.metrics:
            key = info.name + '{' + self.inst_props_string + ",".join(info.props) + '}'
            value = info.value
            try:
                result = col.update_one({'key': key},
                                        {'$set': {
                                            'value': value,
                                            "last_modified": datetime.datetime.utcnow()
                                        }},

                                        upsert=True)
            except:
                pass


class CommandLogger(monitoring.CommandListener):

    def started(self, event):
        logging.info("Command {0.command_name} with request id "
                     "{0.request_id} started on server "
                     "{0.connection_id}".format(event))

    def succeeded(self, event):
        logging.info("Command {0.command_name} with request id "
                     "{0.request_id} on server {0.connection_id} "
                     "succeeded in {0.duration_micros} "
                     "microseconds".format(event))

    def failed(self, event):
        logging.info("Command {0.command_name} with request id "
                     "{0.request_id} on server {0.connection_id} "
                     "failed in {0.duration_micros} "
                     "microseconds".format(event))


monitoring.register(CommandLogger())


class ServerLogger(monitoring.ServerListener):

    def opened(self, event):
        logging.info("Server {0.server_address} added to topology "
                     "{0.topology_id}".format(event))

    def description_changed(self, event):
        previous_server_type = event.previous_description.server_type
        new_server_type = event.new_description.server_type
        if new_server_type != previous_server_type:
            # server_type_name was added in PyMongo 3.4
            logging.info(
                "Server {0.server_address} changed type from "
                "{0.previous_description.server_type_name} to "
                "{0.new_description.server_type_name}".format(event))

    def closed(self, event):
        logging.warning("Server {0.server_address} removed from topology "
                        "{0.topology_id}".format(event))


# monitoring.register(ServerLogger())

class HeartbeatLogger(monitoring.ServerHeartbeatListener):

    def started(self, event):
        logging.info("Heartbeat sent to server "
                     "{0.connection_id}".format(event))

    def succeeded(self, event):
        # The reply.document attribute was added in PyMongo 3.4.
        logging.info("Heartbeat to server {0.connection_id} "
                     "succeeded with reply "
                     "{0.reply.document}".format(event))

    def failed(self, event):
        logging.warning("Heartbeat to server {0.connection_id} "
                        "failed with error {0.reply}".format(event))


# monitoring.register(HeartbeatLogger())

class TopologyLogger(monitoring.TopologyListener):
    healthly = False

    def opened(self, event):
        logging.info("Topology with id {0.topology_id} "
                     "opened".format(event))

    def description_changed(self, event):
        logging.info("Topology description updated for "
                     "topology id {0.topology_id}".format(event))
        previous_topology_type = event.previous_description.topology_type
        new_topology_type = event.new_description.topology_type
        if new_topology_type != previous_topology_type:
            # topology_type_name was added in PyMongo 3.4
            logging.info(
                "Topology {0.topology_id} changed type from "
                "{0.previous_description.topology_type_name} to "
                "{0.new_description.topology_type_name}".format(event))
        # The has_writable_server and has_readable_server methods
        # were added in PyMongo 3.4.
        if not event.new_description.has_writable_server():
            logging.warning("No writable servers available.")
            TopologyLogger.healthly = False
        else:
            TopologyLogger.healthly = True

        if not event.new_description.has_readable_server():
            logging.warning("No readable servers available.")

    def closed(self, event):
        logging.info("Topology with id {0.topology_id} "
                     "closed".format(event))


monitoring.register(TopologyLogger())


class Sender:
    def __init__(self, server='localhost', port=27017, db='info'):
        self.client = None
        self.db = None
        self.import_mongodb(server, port)
        self.chose_db(db)

    def chose_db(self, db_name):
        print('select db ', db_name)
        self.db = self.client[db_name]
        print('select db ', db_name, 'finished')

    def update(self, infos, collection='app_info'):
        # print('start update with value', TopologyLogger.healthly)
        if TopologyLogger.healthly is True:
            infos.update(self.db[collection])
        else:
            print('metrics not updated due to connection failed')

    def import_mongodb(self, server='localhost', port=27017):
        try:
            from pymongo import MongoClient
        except ImportError:
            pass
        else:
            print('connecting to', server, port)
            self.client = MongoClient(server, port,
                                      socketTimeoutMS=100,
                                      connectTimeoutMS=100,
                                      serverSelectionTimeoutMS=100
                                      )
            print('connecting to', server, port, 'finished')


if __name__ == '__main__':
    sender = Sender()
    sender.import_mongodb('localhost')
    sender.chose_db('info')

    # name and value are mandatory for each Info

    order_large = Metric("order", 231, {"range": "large"})
    order_small = Metric("order", 23, {"range": "small"})

    # compose different dimensions to infos
    # second parameter of MetricList is Instance Info, will add to all Infos
    infos = metricList([order_large, order_small], {"instance": "1.1.1.1", 'env': 'prod'})
    sender.update(infos)

    # update state, and push to sender
    order_large.set_value(123)
    order_small.set_value(456)
    sender.update(infos)
