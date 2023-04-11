# -*- coding: utf-8 -*-
from pathlib import Path
import os
from models import Rating
import datetime
import config
from tests.utils import *
import gettext
_local = gettext.gettext

sitespeed_use_docker = config.sitespeed_use_docker


def get_result(sitespeed_use_docker, arg):

    result = ''
    if sitespeed_use_docker:
        dir = Path(os.path.dirname(
            os.path.realpath(__file__)) + os.path.sep).parent
        data_dir = dir.resolve()

        bashCommand = "docker run --rm -v {1}:/sitespeed.io sitespeedio/sitespeed.io:latest {0}".format(
            arg, data_dir)

        import subprocess
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        result = str(output)
    else:
        import subprocess

        bashCommand = "node node_modules{1}sitespeed.io{1}bin{1}sitespeed.js {0}".format(
            arg, os.path.sep)

        process = subprocess.Popen(
            bashCommand.split(), stdout=subprocess.PIPE)

        output, error = process.communicate()
        result = str(output)

    return result


def run_test(_, langCode, url):
    """
    Checking an URL against Sitespeed.io (Docker version). 
    For installation, check out:
    - https://hub.docker.com/r/sitespeedio/sitespeed.io/
    - https://www.sitespeed.io
    """
    language = gettext.translation(
        'performance_sitespeed_io', localedir='locales', languages=[langCode])
    language.install()
    _local = language.gettext

    print(_local('TEXT_RUNNING_TEST'))

    print(_('TEXT_TEST_START').format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    rating = Rating(_)
    result_dict = {}
    (desktop_rating, desktop_result_dict) = validate_on_desktop(url, _, _local)
    rating += desktop_rating
    result_dict.update(desktop_result_dict)

    (mobile_rating, mobile_result_dict) = validate_on_mobile(url, _, _local)
    rating += mobile_rating
    result_dict.update(mobile_result_dict)

    # result = validate_no_javascript(url)
    # result = validate_no_external_domain(url)

    print(_('TEXT_TEST_END').format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    return (rating, result_dict)

# validate_no_javascript
# validate_no_external_domain


def validate_on_desktop(url, _, _local):
    arg = '--shm-size=1g -b chrome --connectivity.profile native --visualMetrics true --plugins.remove screenshot --speedIndex true --xvfb --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
        config.sitespeed_iterations, url)
    if 'nt' in os.name:
        arg = '--shm-size=1g -b chrome --connectivity.profile native --visualMetrics true --plugins.remove screenshot --speedIndex true --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
            config.sitespeed_iterations, url)

    result = get_result_dict(get_result(sitespeed_use_docker, arg), 'desktop')
    rating = rate_result_dict(result, 'desktop', _, _local)

    return (rating, result)


def validate_on_mobile(url, _, _local):
    arg = '--shm-size=1g -b chrome --mobile true --connectivity.profile 3gfast --visualMetrics true --plugins.remove screenshot --speedIndex true --xvfb --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
        config.sitespeed_iterations, url)
    if 'nt' in os.name:
        arg = '--shm-size=1g -b chrome --mobile true --connectivity.profile 3gfast --visualMetrics true --plugins.remove screenshot --speedIndex true --browsertime.videoParams.createFilmstrip false --browsertime.chrome.args ignore-certificate-errors -n {0} {1}'.format(
            config.sitespeed_iterations, url)

    result = get_result_dict(get_result(sitespeed_use_docker, arg), 'mobile')
    rating = rate_result_dict(result, 'mobile', _, _local)

    return (rating, result)


def rate_result_dict(result_dict, mode, _, _local):
    points = int(result_dict['Points'])

    review = ''

    review_overall = ''
    if points >= 5.0:
        review_overall = _local('TEXT_REVIEW_VERY_GOOD')
    elif points >= 4.0:
        review_overall = _local('TEXT_REVIEW_IS_GOOD')
    elif points >= 3.0:
        review_overall = _local('TEXT_REVIEW_IS_OK')
    elif points > 1.0:
        review_overall = _local('TEXT_REVIEW_IS_BAD')
    elif points <= 1.0:
        review_overall = _local('TEXT_REVIEW_IS_VERY_BAD')

    del result_dict['Points']

    # review += '- Speedindex: {}\n'.format(result_dict['SpeedIndex'])

    rating = Rating(_)
    rating.set_overall(points, review_overall.replace(
        '- ', '- {0} '.format(mode)))
    rating.set_performance(points, review)

    review = rating.performance_review
    for pair in result_dict.items():
        key = pair[0]
        value = pair[1]
        review += '- {0}: {1}\r\n'.format(key, value)

    # if 's' in result_dict['Load']:
    #     review += _local("TEXT_REVIEW_LOAD_TIME").format(result_dict['Load'])
    # else:
    #     review += _local("TEXT_REVIEW_LOAD_TIME_SECONDS").format(
    #         result_dict['Load'])

    # review += _local("TEXT_REVIEW_NUMBER_OF_REQUESTS").format(
    #     result_dict['Requests'])

    rating.performance_review = review
    # rating.overview_review = review_overall
    return rating


def get_result_dict(data, mode):
    result_dict = {}
    tmp_dict = {}
    regex = r"(?P<name>TTFB|DOMContentLoaded|firstPaint|FCP|LCP|Load|TBT|CLS|FirstVisualChange|SpeedIndex|VisualComplete85|LastVisualChange)\:[ ]{0,1}(?P<value>[0-9\.ms]+)"
    matches = re.finditer(regex, data, re.MULTILINE)

    for matchNum, match in enumerate(matches, start=1):
        name = match.group('name')
        value = match.group('value')
        # print('PAIR: ', name, value, '± 10')
        if name not in tmp_dict:
            tmp_dict[name] = list()
        tmp_dict[name].append(value)

    for pair in tmp_dict.items():
        key = pair[0]
        values = pair[1]
        biggest = 0
        total = 0
        value_range = 0
        str_result = ''
        result = 0
        # print(key)
        for value in values:
            number = 0
            if 'ms' in value:
                number = float(value.replace('ms', ''))
            elif 's' in value:
                number = float(
                    value.replace('s', '')) * 1000
            total += number
            if number > biggest:
                biggest = number
            # print('  ', number, total)
        value_count = len(values)
        if value_count < 2:
            value_range = 0
            result = total
        else:
            median = total / value_count
            value_range = biggest - median
            result = median

        str_result = '{0:.2f}ms (±{1:.2f}ms)'.format(result, value_range)
        if 'SpeedIndex' in key:
            points = 5.0

            adjustment = 500
            if 'mobile' in mode:
                adjustment = 1500

            # give 0.5 seconds in credit
            speedindex_adjusted = result - adjustment
            if speedindex_adjusted <= 0:
                # speed index is 500 or below, give highest score
                points = 5.0
            else:
                points = 5.0 - (speedindex_adjusted / 1000)

            result_dict['Points'] = points
        # print('  ', result)
        result_dict['{0} {1}'.format(mode, key)] = str_result
    return result_dict
