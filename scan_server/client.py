from pygvm.exceptions import AuthenticationError
from pygvm.pygvm import Pygvm
from gvm.connections import UnixSocketConnection, TLSConnection
from gvm.protocols.latest import Gmp
from gvm.transforms import EtreeTransform
from config import settings, logger
from zapv2 import ZAPv2

def get_gvm_conn() -> Pygvm:
    connection = None
    if settings.gvmdtype == "unix":
        unixsockpath = settings.unixsockpath
        connection = UnixSocketConnection(path=unixsockpath)
    elif settings.gvmdtype == "tls":
        capath = settings.tlscapath
        certpath = settings.tlscertpath
        keypath = settings.tlskeypath
        connection = TLSConnection(hostname=settings.gvmdhost, 
                                    port=settings.gvmdport, 
                                    cafile=capath,
                                    certfile=certpath,
                                    keyfile=keypath)
    transform = EtreeTransform()
    gmp = Gmp(connection, transform=transform)
    pyg = Pygvm(gmp=gmp, username=settings.username, passwd=settings.password)
    if pyg.checkauth() is False:
        raise AuthenticationError()
    return pyg


def get_zap_conn() -> ZAPv2:
    zap = ZAPv2(proxies={'http':settings.http_proxy}, apikey=settings.apikey)
    res = zap.pscan.set_max_alerts_per_rule(20)
    if res != 'OK':
        raise Exception("Set max alerts per rule failed.") 
    return zap

def handle_zap_task(zap: ZAPv2, running_status:str, target:str):
    if running_status == 'spider':
        progress = int(zap.spider.status(0))
        # 传统爬虫完成进入Ajax爬虫
        if progress >= 100:
            zap.ajaxSpider.set_option_max_crawl_depth(5)
            zap.ajaxSpider.set_option_max_duration(10)
            zap.ajaxSpider.set_option_browser_id('htmlunit')
            zap.ajaxSpider.set_option_number_of_browsers(settings.zap_max_thread)
            res = zap.ajaxSpider.scan(target)
            if res != 'OK':
                raise Exception("AjaxSpider begin failed.")
            running_status = 'ajaxspider'
    # 2. 进入ajax爬虫期间
    if running_status == 'ajaxspider':
        status = zap.ajaxSpider.status
        # ajax爬虫完成进入主动扫描
        if status != 'running':
            zap.ascan.set_option_max_scan_duration_in_mins(15)
            zap.ascan.set_option_max_rule_duration_in_mins(1)
            # 控制线程并发数
            zap.ascan.set_option_thread_per_host(settings.zap_max_thread)
            # 主动扫描加速
            zap.ascan.set_option_max_alerts_per_rule(1)
            zap.ascan.set_option_max_results_to_list(1)
            zap.ascan.set_option_max_chart_time_in_mins(0)
            res = zap.ascan.scan(target)
            # url无效，扫描结束
            if res == 'url_not_found':
                running_status = 'failed'
                return running_status, res
            elif int(res) != 0:
                raise Exception(f"Active scan failed.")
            else:
                running_status = 'active'
    # 3. 进入主动扫描期间
    if running_status == 'active':
        progress = int(zap.ascan.status(0))
        # 主动扫描完成，进入被动扫描
        if progress >= 100:
            pscan = int(zap.pscan.records_to_scan)
            if pscan == 0:
                running_status = 'done'
            else:
                running_status = 'passive'
    # 4. 进入passive扫描期间
    if running_status == 'passive':
        pscan = int(zap.pscan.records_to_scan)
        # 快速退出passive期间
        if pscan < 10:
            running_status = 'done'
    return running_status, None
    
