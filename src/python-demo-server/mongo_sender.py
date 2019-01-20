import datetime
class Info:
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

class InfoList:
    def __init__(self, infos, instanceInfo):
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
        self.infos = infos
        
    def update(self, col):        
        # lines = []
        import pymongo
        for info in self.infos:
            key = info.name + '{' + self.inst_props_string + ",".join(info.props) + '}'
            value = info.value
            try:
                result = col.update_one( {'key': key},
                    {'$set':{
                        'value': value,
                        "last_modified": datetime.datetime.utcnow()
                    }},
                    
                    upsert=True )
                # print(info.__dict__)
            except:
                pass

    
class Sender:
    def __init__(self, server='localhost', port=27017, db = 'info'):
        self.client = None
        self.db = None
        self.import_mongodb(server, port)
        self.chose_db(db)
    
    def chose_db(self, db_name):
        print('select db ', db_name)
        self.db = self.client[db_name]
        print('select db ', db_name, 'finished')

    def update(self, infos, collection='app_info'):
        infos.update(self.db[collection])

    def import_mongodb(self, server='localhost', port=27017):
        try:
            from pymongo import MongoClient
        except ImportError:
            pass
        else:
            print('connecting to', server, port)
            self.client = MongoClient(server, port)
            print('connecting to', server, port, 'finished')
            

if __name__ == '__main__':
    sender = Sender()
    sender.import_mongodb('localhost')
    sender.chose_db('info')

    # name and value are mandatory for each Info

    order_large = Info("order", 231,{"range": "large"})
    order_small = Info("order", 23, {"range": "small"})
    
    # compose different dimensions to infos
    # second parameter of InfoList is Instance Info, will add to all Infos
    infos = InfoList([order_large, order_small], {"instance": "1.1.1.1", 'env':'prod'})
    sender.update(infos)

    # update state, and push to sender
    order_large.set_value(123)
    order_small.set_value(456)
    sender.update(infos)
