"""
Support environment variables:
TESTRAIL_URL=https://example.testrail.com/
TESTRAIL_EMAIL=example@mail.com
TESTRAIL_PASSWORD=password
"""
import os
import json

import matplotlib.pyplot as plt
import numpy as np
from testrail import APIClient, APIError
from mappings import USERS
from datetime import datetime, timedelta

client = APIClient(os.environ.get('TESTRAIL_URL'))
client.user = os.environ.get('TESTRAIL_USER_EMAIL')
client.password = os.environ.get('TESTRAIL_USER_PASSWORD')
WEEKS_REPORT = 2


def reporter(weeks=0):
    current_date = datetime.now() - timedelta(weeks=weeks)
    projects = client.send_get(f'get_projects')['projects']
    last_legacy_project_id = 43

    report = {}
    user_report = {}
    for user_id, user_name in USERS.items():
        user_report.update({user_name: {}})

    for project in projects:
        if project["id"] > last_legacy_project_id:
            try:
                new_cases = client.send_get(
                    uri=f'/get_cases/{project["id"]}'
                        f'&created_after={int(current_date.timestamp())}'
                        f'&group_by=cases:created_by')['cases']
                updated_cases = client.send_get(
                    uri=f'/get_cases/{project["id"]}'
                        f'&updated_after={int(current_date.timestamp())}'
                        f'&group_by=cases:created_by')['cases']
                report.update({project['name']: {
                    'new_cases': new_cases,
                    'updated_cases': updated_cases}})
            except APIError:
                pass

    for user in USERS:
        total_cases_all_projects = 0
        for key, value in report.items():
            proj_cases_count = 0
            proj_cases_updated_count = 0
            # переписать через filter()
            for case in value['new_cases']:
                if user == case['created_by']:
                    proj_cases_count += 1
            for case in value['updated_cases']:
                if user == case['updated_by']:
                    proj_cases_updated_count += 1
            proj_updated_only = proj_cases_updated_count - proj_cases_count
            proj_total = proj_cases_count + proj_updated_only
            user_report[USERS[user]].update(
                {
                    key: {'new': proj_cases_count,
                          'updated': proj_updated_only,
                          'total': proj_total
                          },
                    'total_cases_all_projects': total_cases_all_projects
                }
            )
            total_cases_all_projects += proj_total
        user_report[USERS[user]].update({'total_cases_all_projects': total_cases_all_projects})
    with open("report.json", 'w') as file:
        file.write(json.dumps(user_report))

    return user_report


def histogram_generator(report: dict):
    # make data:
    testers = list(report.keys())
    tests = list(x['total_cases_all_projects'] for x in report.values())
    y_pos = np.arange(len(testers))

    # plot
    fig, ax = plt.subplots()
    rects = ax.barh(y_pos, tests, align='center')

    ax.set_yticks(y_pos, labels=testers)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.bar_label(rects, padding=3)
    ax.set_xlabel('Test cases')
    ax.set_title(f'New test cases for {WEEKS_REPORT} weeks')
    fig.set_size_inches(h=6, w=12, forward=True)
    plt.show()


histogram_generator(reporter(weeks=WEEKS_REPORT))

