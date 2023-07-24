import mysql.connector
from dotenv.main import load_dotenv
import os
import json

load_dotenv()

mydb = mysql.connector.connect(
    host=os.environ['HOST_DB'],
    user=os.environ['USER_DB'],
    password=os.environ['PASS_DB'],
    database=os.environ['NAME_DB']

)


def get_info(feature, id_):
    mydb.reconnect()
    cnx = mydb.cursor()
    query = f"SELECT {feature} FROM trained_model WHERE id = {id_}"

    print(query)
    cnx.execute(query)
    return cnx.fetchone()


def update_status(id_, status):
    mydb.reconnect()
    cn = mydb.cursor()
    query = "UPDATE trained_model SET status = '{status}' WHERE id = {id}".format(status=status, id=id_)
    cn.execute(query)
    mydb.commit()


def update(id_tb, col_tb, value_tb):
    mydb.reconnect()
    cn = mydb.cursor()
    query = "UPDATE trained_model SET {col} = '{value}' WHERE id = {id}".format(id=id_tb, col=col_tb, value=value_tb)
    cn.execute(query)
    mydb.commit()


def get_train(id_):
    mydb.reconnect()
    cn = mydb.cursor()
    query = f"SELECT name ,epoch,batch_size,dataset_keys,test_dataset_keys,trained_model_id ,status,labels FROM trained_model train WHERE id ={id_}"
    cn.execute(query)
    result = cn.fetchone()
    if result is not None:
        result = result
    name, epoch, batch_size, train_dataset, test_dataset, pretrain_id, status, labels = result
    if pretrain_id is not None:

        query_pretrain = f"SELECT train.name  FROM trained_model train WHERE id ={pretrain_id}"
        cn.execute(query_pretrain)
        result = cn.fetchone()
        name_pretrain = result[0]
    else:
        name_pretrain = None

    return name, epoch, batch_size, train_dataset, test_dataset, name_pretrain, status, labels


def update_epochs(id_, current_epochs):
    mydb.reconnect()
    cn = mydb.cursor()
    query = "UPDATE trained_model SET current_epoch = {current_epochs}" \
            " WHERE id = {id}".format(current_epochs=current_epochs, id=id_)
    cn.execute(query)
    mydb.commit()


def get_report(id_):
    mydb.reconnect()
    cn = mydb.cursor()
    query = f"SELECT tm.name,report.dataset_keys,tm.labels,report.status \
            FROM report \
            JOIN trained_model tm on tm.id = report.trained_model_id \
            WHERE report.id ={id_}\
            "
    cn.execute(query)
    return cn.fetchone()
def update_report(content,id):

    doc = json.dumps(content)

    mydb.reconnect()
    cn = mydb.cursor()
    sql = """
        UPDATE report 
        SET content = %s,status = 'SUCCESS'
        WHERE id = %s
    """

    cn.execute(sql, (doc, id))

    mydb.commit()

def update_process(id_,value_,table):
    mydb.reconnect()
    cn = mydb.cursor()
    query = f"UPDATE {table} SET process_id = '{value_}' ,status = 'STARTED' WHERE id = {id_}"
    cn.execute(query)
    mydb.commit()


def update_status(id_,status_,table):
    mydb.reconnect()
    cn = mydb.cursor()
    query = f"UPDATE {table} SET status = '{status_}' WHERE id = {id_}"
    cn.execute(query)
    mydb.commit()


def get_processid(id_,table):
    mydb.reconnect()
    cnx = mydb.cursor()
    query = f"SELECT process_id FROM {table} WHERE id = {id_}"
    cnx.execute(query)
    return cnx.fetchone()





    


