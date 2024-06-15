from fastapi import APIRouter
from client import get_gvm_conn
from config import logger

router = APIRouter(
    prefix="/gvm",  # 前缀只在这个模块中使用
    tags=["gvmtasks"],
)


@router.get("/hello")
async def helloworld():
    return {'ok': True}


@router.get("/get_task")
async def get_task(running_id: str):
    try:
        pygvm = get_gvm_conn()
        task = pygvm.get_task(task_id=running_id)
        progress = task['progress']
        status = task['status']
        return {'ok': True, 'progress': progress, 'running_status': status}
    except Exception as e:
        logger.error('Faild to get gvm task: ' + str(e))
        return {'ok': False, 'errmsg': str(e)}
    finally:
        pygvm.disconnect()
        

@router.post("/create_task")
async def create_task(id:str, target:str):
    try:
        pygvm = get_gvm_conn()
        # 0. 获取目标
        target_host = [target]
        # 1. 创建目标
        target = pygvm.create_target('target_'+id, hosts=target_host, port_list_id='33d0cd82-57c6-11e1-8ed1-406186ea4fc5')
        target_id = target['@id']
        # 2. 创建任务
        task = pygvm.create_task(name=f"task_{id}",target_id=target_id, 
                          config_id='daba56c8-73ec-11df-a475-002264764cea', 
                          scanner_id='08b69003-5fc2-4037-a479-93b440211c73',
                            preferences={'assets_min_qod' : 30})
        task_id = task['@id']
        # 3. 开始任务
        pygvm.start_task(task_id=task_id)
        return {'ok': True, 'running_id': task_id}
    except Exception as e:
        logger.error('Faild to create gvm task: ' + str(e))
        return {'ok': False, 'errmsg': str(e)}
    finally:
        pygvm.disconnect()


@router.delete("/delete_task")
async def delete_task(running_id: str):
    try:
        pygvm = get_gvm_conn()
        # 1. 停止task
        pygvm.stop_task(task_id=running_id)
        # 2. 删除task
        pygvm.delete_task(task_id=running_id)
        return {'ok': True}
    except Exception as e:
        logger.error('Faild to delete gvm task: ' + str(e))
        return {'ok': False, 'errmsg': str(e)}
    finally:
        pygvm.disconnect()


@router.get("/get_report")
async def get_report(running_id: str):
    try:
        pygvm = get_gvm_conn()
        # 0. 获取task对应report
        report = pygvm.list_reports(task_id=running_id)[0]
        report_id = report['@id']
        # 1. 获取report文件内容
        content = pygvm.get_report(report_id=report_id, report_format_name='PDF', 
                       filter_str='apply_overrides=0 levels=hml rows=1000 min_qod=30 first=1 sort-reverse=severity')
        return {'ok': True, 'content': content}
    except Exception as e:
        logger.error('Faild to get gvm report: ' + str(e))
        return {'ok': False, 'errmsg': str(e)}
    finally:
        pygvm.disconnect()
