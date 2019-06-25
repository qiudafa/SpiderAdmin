# -*- coding: utf-8 -*-

# @Date    : 2019-06-25
# @Author  : Peng Shiyu

from flask import Blueprint, jsonify, request

from api_app import scrapyd_utils

from api_app.scrapyd_api import ScrapydAPI
from api_app.scrapyd_utils import get_server_status, cancel_all_spider

from tinydb import TinyDB, Query

try:
    from config import SCRAPYD_SERVERS
except:
    from defualt_config import SCRAPYD_SERVERS

api_app = Blueprint(name="api", import_name=__name__)
db = TinyDB("server.db")
user_server_table = db.table("user_servers")
query = Query()


def get_servers():
    user_servers = user_server_table.all()

    defualt_servers = [
        {
            "server_name": server_name,
            "server_host": server_host
        }
        for server_name, server_host in SCRAPYD_SERVERS
    ]

    user_servers.extend(defualt_servers)
    return user_servers


@api_app.route("/servers")
def servers():
    return jsonify(get_servers())


@api_app.route("/addServer", methods=["POST"])
def add_server():
    server_host = request.json.get("server_host")
    server_name = request.json.get("server_name")
    user_server_table.insert(
        {
            "server_name": server_name,
            "server_host": server_host
        }
    )
    return jsonify({
        "message": "添加成功"
    })


@api_app.route("/removeServer", methods=["POST"])
def remove_server():
    server_host = request.json.get("server_host")
    server_name = request.json.get("server_name")
    server = {
        "server_name": server_name,
        "server_host": server_host
    }
    print(server)

    result = user_server_table.remove(
        (query.server_name == server_name) &
        (query.server_host == server_host)
    )
    if result:
        message = "移除成功"
        message_type = "success"
    else:
        message = "移除失败"
        message_type = "warning"
    return jsonify({
        "message": message,
        "message_type": message_type
    })


@api_app.route("/ServerStatus")
def servers_status():
    return jsonify(get_server_status(get_servers()))


@api_app.route("/listProjects")
def list_projects():
    """
    显示项目
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")

    scrapyd = ScrapydAPI(server_host)
    projects = scrapyd.list_projects()

    lst = []
    for project in projects:
        versions = scrapyd.list_versions(project)
        for version in versions:
            item = {
                "project_name": project,
                "human_version": scrapyd_utils.format_version(version),
                "version": version
            }
            lst.append(item)

    data = {
        "server_name": server_name,
        "server_host": server_host,
        "projects": lst

    }

    return jsonify(data)


@api_app.route("/listSpiders")
def list_spiders():
    """
    查看爬虫列表
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")

    scrapyd = ScrapydAPI(server_host)
    spiders = scrapyd.list_spiders(project_name)

    data = {
        "server_name": server_name,
        "server_host": server_host,
        "project_name": project_name,
        "spiders": [{"spider_name": spider} for spider in spiders]
    }
    return jsonify(data)


@api_app.route("/schedule")
def schedule():
    """
    调度运行爬虫
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")
    spider_name = request.args.get("spider_name")

    scrapyd = ScrapydAPI(server_host)
    result = scrapyd.schedule(project_name, spider_name)

    return jsonify({"message": result})


@api_app.route("/listJobs")
def list_jobs():
    """
    查看任务
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")

    scrapyd = ScrapydAPI(server_host)
    jobs = scrapyd.list_jobs(project_name)
    lst = []
    for job_status, job_list in jobs.items():
        for job in job_list:
            item = {
                "status": job_status,
                "spider": job["spider"],
                "start_time": scrapyd_utils.format_time(job.get("start_time", "")),
                "end_time": scrapyd_utils.format_time(job.get("end_time", "")),
                "timestamp": scrapyd_utils.get_timestamp(job.get("end_time"), job.get("start_time")),
                "job_id": job["id"]
            }
            lst.append(item)

    data = {
        "server_host": server_host,
        "server_name": server_name,
        "project_name": project_name,
        "jobs": lst,
    }

    return jsonify(data)


@api_app.route("/log")
def log():
    """
    查看日志
    """
    server_host = request.args.get("server_host")
    project_name = request.args.get("project_name")
    spider_name = request.args.get("spider_name")
    job_id = request.args.get("job_id")

    url = scrapyd_utils.get_log_url(server_host, project_name, spider_name, job_id)
    return scrapyd_utils.get_log(url)


@api_app.route("/cancelAll")
def cancel_all():
    server_host = request.args.get("server-host")
    cancel_all_spider(server_host)
    return jsonify({
        "message": "删除成功!",
        "status": 200
    })


@api_app.route("/cancel")
def cancel():
    """
    取消爬虫运行
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")
    job_id = request.args.get("job_id")

    scrapyd = ScrapydAPI(server_host)
    result = scrapyd.cancel(project_name, job_id)

    return jsonify({"message": result})


@api_app.route("/deleteVersion")
def delete_version():
    """
    删除项目
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")
    version = request.args.get("version")
    scrapyd = ScrapydAPI(server_host)
    result = scrapyd.delete_version(project_name, version)
    return jsonify(
        {
            "message": result
        }
    )