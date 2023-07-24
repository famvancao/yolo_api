import _queue
import os.path
import signal
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
import uvicorn
from Classes import ID
from database import get_info, update_status, update, get_train, get_report,update_process,update_status,get_processid
import MESSAGE
from dotenv.main import load_dotenv
from multiprocessing import Process, Queue
import multiprocessing as mp
from Funtions.functions import plot_results, check_resources, train_yolo, create_total_dataset,report_model


load_dotenv()
app = FastAPI()
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
items_queue = Queue(maxsize=int(os.environ["MAX_QUEUE_SIZE"]))


def get_api_key(api_key: str = Security(api_key_header), ) -> str:
    key = os.environ["API_KEYS"]
    if api_key == key:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key")


def consumer(queue_):
    while True:
        try:
            item, task_type = queue_.get(timeout=0.01)
            if item is None:
                continue
            if task_type == "train":
                batch_size = item[4]
                id_train = item[-1 - 1]
                update_status(id_train,"PENDING","trained_model")

                while not check_resources(batch_size):
                    pass

                task_running = Process(target=train_yolo, args=(item,))
                task_running.start()
                update_process(id_train,task_running.pid,"trained_model")



 
            elif task_type == "eval":
                pretrained_name, datasets,classes,id = item
                update_status(id,"PENDING","report")


                while not check_resources(20):
                    pass

                task_running = Process(target=report_model, args=(pretrained_name, datasets,classes,id,))
                task_running.start()
                update_process(id,task_running.pid,"report")

        except _queue.Empty:
            pass


@app.on_event('startup')
async def on_startup():
    print("start")
    Process(target=consumer, args=(items_queue,)).start()


@app.post("/train")
async def train(id_train: ID, api_key: str = Security(get_api_key)):
    global items_queue
    # try:
    id_train = id_train.id

    info = get_train(id_train)

    if info is None:
        raise HTTPException(status_code=404,
                            detail=MESSAGE.ERROR_TRAIN_NOT_FOUND)

    name, epoch, batch_size, train_dataset, test_dataset, name_pretrain, status_, labels = info
    train_dataset = train_dataset.split(',')
    test_dataset = test_dataset.split(',')

    if len(train_dataset) > 1:
        create_total_dataset(f'synthetic_{name}', train_dataset)
        train_dataset = name
    else:
        train_dataset = train_dataset[0]

    if len(test_dataset) > 1:
        create_total_dataset(f'synthetic_{name}_val', test_dataset)
        test_dataset = f'{name}_val'
    else:
        test_dataset = test_dataset[0]

    # if status_ in ["NOT_RUNNING", "REVOKED"]:
    train_path = os.path.join(os.environ['PATH_DATA'], train_dataset)
    val_path = os.path.join(os.environ['PATH_DATA'], test_dataset)

    print("name_pretrain", name_pretrain)
    if name_pretrain is not None:
        pretrained = os.path.join(*[os.environ['WEIGHTS_PATH'], name_pretrain, 'weights/best.pt'])
    else:
        pretrained = ""

    print(train_path)
    print(val_path)

    if os.path.exists(train_path) and os.path.exists(val_path):

        items_queue.put([(train_path, val_path, pretrained, epoch, batch_size, name, id_train, labels), "train"])

        update(id_train, "status", "STARTED")
        return {"message": MESSAGE.SUCCESSFULLY}
    else:
        raise HTTPException(status_code=404,
                            detail=MESSAGE.ERROR_FILE_NOT_FOUND)
    # else:
    #     raise HTTPException(status_code=404,
    #                         detail=MESSAGE.ERROR_TASK_STATUS_BLOCKED)



@app.post("/stop_train")
async def stop_train(id_trained: ID, api_key: str = Security(get_api_key)):
    try:
        id_trained = id_trained.id
        result = get_processid(id_trained,'trained_model')
        if result is not None:
            task_id = result[0]

            print(task_id)
            os.kill(int(task_id), signal.SIGKILL)
            update_status(task_id,"REVOKED","trained_model")
            return {"message": MESSAGE.SUCCESSFULLY}

        else:
            raise HTTPException(status_code=404,
                                detail=MESSAGE.ERROR_TRAIN_NOT_FOUND)
    except ProcessLookupError:
        raise HTTPException(
            status_code=400, detail=MESSAGE.ERROR_TASK_NOT_START
        )
@app.post("/stop_report_model")
async def stop_train(id_trained: ID, api_key: str = Security(get_api_key)):
    try:
        id_trained = id_trained.id
        result = get_processid(id_trained,'report')
        if result is not None:
            task_id = result[0]

            print(task_id)
            os.kill(int(task_id), signal.SIGKILL)
            update_status(task_id,"REVOKED","report")
            return {"message": MESSAGE.SUCCESSFULLY}

        else:
            raise HTTPException(status_code=404,
                                detail=MESSAGE.ERROR_TRAIN_NOT_FOUND)
    except ProcessLookupError:
        raise HTTPException(
            status_code=400, detail=MESSAGE.ERROR_TASK_NOT_START
        )
    

@app.get("/visualization")
async def visualization(id: int, api_key: str = Security(get_api_key)):
    try:
        get_db = get_info('name,status,current_epoch', id)
        if get_db is None:
            raise HTTPException(status_code=404,
                                detail=MESSAGE.ERROR_TRAIN_NOT_FOUND)
        name_db, status_,current_epoch = get_db
        if status_ not in ['STARTED', 'SUCCESS', 'FAILURE']:
            raise HTTPException(status_code=404,
                                detail=MESSAGE.ERROR_TASK_STATUS_BLOCKED)
        path_visual = os.path.join(os.environ['WEIGHTS_PATH'], name_db)

        path_csv = os.path.join(*[os.environ['WEIGHTS_PATH'], name_db, 'results.csv'])

        if status !=['SUCCESS']:
            if current_epoch>1:
                plot_results(path_csv.format(name_db), name=name_db)
            else:
                raise HTTPException(status_code=400,
                            detail=MESSAGE.ERROR_FILE_NOT_FOUND)


        return {"message": MESSAGE.SUCCESSFULLY}
    except FileNotFoundError:
        raise HTTPException(status_code=404,
                            detail=MESSAGE.ERROR_FILE_NOT_FOUND)
    except AssertionError:
        raise HTTPException(status_code=404,
                            detail=MESSAGE.ERROR_FILE_CSV_NOT_FOUND)

@app.post("/report_model")
async def report(request: ID):
    report_id = request.id
    info = get_report(report_id)
    if info is None:
        raise HTTPException(status_code=404,
                            detail=MESSAGE.ERROR_REPORT_NOT_FOUND)

    weight, datasets, labels,status = info

    if status == "NOT_RUNNING":

        items_queue.put([(weight, datasets.split(','), labels.split(','),report_id), 'eval'])
        return {"message": MESSAGE.SUCCESSFULLY}
    else:
        raise HTTPException(
            status_code=400, detail=MESSAGE.ERROR_TASK_NOT_START
        )



if __name__ == "__main__":
    uvicorn.run("backend:app", host='0.0.0.0', port=5555, reload=True)
     