# coding: utf-8

"""
    College Football Data API

    This is an API for accessing all sorts of college football data.  It currently has a wide array of data ranging from play by play to player statistics to game scores and more.  # noqa: E501

    OpenAPI spec version: 1.12.0
    Contact: admin@collegefootballdata.com
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


from __future__ import absolute_import

import re  # noqa: F401

# python 2 and python 3 compatibility library
import six

from PyCollegeFootballData.api_client import ApiClient


class PlaysApi(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    Ref: https://github.com/swagger-api/swagger-codegen
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

    def get_play_stat_types(self, **kwargs):  # noqa: E501
        """Get play stat type lists  # noqa: E501

        Type of play stats  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_play_stat_types(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: list[PlayStatType]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.get_play_stat_types_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.get_play_stat_types_with_http_info(**kwargs)  # noqa: E501
            return data

    def get_play_stat_types_with_http_info(self, **kwargs):  # noqa: E501
        """Get play stat type lists  # noqa: E501

        Type of play stats  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_play_stat_types_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: list[PlayStatType]
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_play_stat_types" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            '/play/stat/types', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='list[PlayStatType]',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_play_stats(self, **kwargs):  # noqa: E501
        """Get play statistics  # noqa: E501

        Gets player stats associated by play (limit 1000)  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_play_stats(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param int year: Year filter
        :param int week: Week filter
        :param str team: Team filter
        :param int game_id: gameId filter (from /games endpoint)
        :param int athlete_id: athleteId filter (from /roster endpoint)
        :param int stat_type_id: statTypeId filter (from /play/stat/types endpoint)
        :return: list[PlayStat]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.get_play_stats_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.get_play_stats_with_http_info(**kwargs)  # noqa: E501
            return data

    def get_play_stats_with_http_info(self, **kwargs):  # noqa: E501
        """Get play statistics  # noqa: E501

        Gets player stats associated by play (limit 1000)  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_play_stats_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param int year: Year filter
        :param int week: Week filter
        :param str team: Team filter
        :param int game_id: gameId filter (from /games endpoint)
        :param int athlete_id: athleteId filter (from /roster endpoint)
        :param int stat_type_id: statTypeId filter (from /play/stat/types endpoint)
        :return: list[PlayStat]
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ['year', 'week', 'team', 'game_id', 'athlete_id', 'stat_type_id']  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_play_stats" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []
        if 'year' in params:
            query_params.append(('year', params['year']))  # noqa: E501
        if 'week' in params:
            query_params.append(('week', params['week']))  # noqa: E501
        if 'team' in params:
            query_params.append(('team', params['team']))  # noqa: E501
        if 'game_id' in params:
            query_params.append(('gameId', params['game_id']))  # noqa: E501
        if 'athlete_id' in params:
            query_params.append(('athleteId', params['athlete_id']))  # noqa: E501
        if 'stat_type_id' in params:
            query_params.append(('statTypeId', params['stat_type_id']))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            '/play/stats', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='list[PlayStat]',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_play_types(self, **kwargs):  # noqa: E501
        """Get play type list  # noqa: E501

        Types of plays  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_play_types(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: list[PlayType]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.get_play_types_with_http_info(**kwargs)  # noqa: E501
        else:
            (data) = self.get_play_types_with_http_info(**kwargs)  # noqa: E501
            return data

    def get_play_types_with_http_info(self, **kwargs):  # noqa: E501
        """Get play type list  # noqa: E501

        Types of plays  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_play_types_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :return: list[PlayType]
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = []  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_play_types" % key
                )
            params[key] = val
        del params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            '/play/types', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='list[PlayType]',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def get_plays(self, year, **kwargs):  # noqa: E501
        """Get play information. Requires either a week or team to be specified.  # noqa: E501

        Play results  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_plays(year, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param int year: Year filter (required)
        :param str season_type: Season type filter
        :param int week: Week filter (required if team, offense, or defense, not specified)
        :param str team: Team filter
        :param str offense: Offensive team filter
        :param str defense: Defensive team filter
        :param str conference: Conference filter
        :param str offense_conference: Offensive conference filter
        :param str defense_conference: Defensive conference filter
        :param int play_type: Play type filter
        :return: list[Play]
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.get_plays_with_http_info(year, **kwargs)  # noqa: E501
        else:
            (data) = self.get_plays_with_http_info(year, **kwargs)  # noqa: E501
            return data

    def get_plays_with_http_info(self, year, **kwargs):  # noqa: E501
        """Get play information. Requires either a week or team to be specified.  # noqa: E501

        Play results  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.get_plays_with_http_info(year, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param int year: Year filter (required)
        :param str season_type: Season type filter
        :param int week: Week filter (required if team, offense, or defense, not specified)
        :param str team: Team filter
        :param str offense: Offensive team filter
        :param str defense: Defensive team filter
        :param str conference: Conference filter
        :param str offense_conference: Offensive conference filter
        :param str defense_conference: Defensive conference filter
        :param int play_type: Play type filter
        :return: list[Play]
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ['year', 'season_type', 'week', 'team', 'offense', 'defense', 'conference', 'offense_conference', 'defense_conference', 'play_type']  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method get_plays" % key
                )
            params[key] = val
        del params['kwargs']
        # verify the required parameter 'year' is set
        if ('year' not in params or
                params['year'] is None):
            raise ValueError("Missing the required parameter `year` when calling `get_plays`")  # noqa: E501

        collection_formats = {}

        path_params = {}

        query_params = []
        if 'season_type' in params:
            query_params.append(('seasonType', params['season_type']))  # noqa: E501
        if 'year' in params:
            query_params.append(('year', params['year']))  # noqa: E501
        if 'week' in params:
            query_params.append(('week', params['week']))  # noqa: E501
        if 'team' in params:
            query_params.append(('team', params['team']))  # noqa: E501
        if 'offense' in params:
            query_params.append(('offense', params['offense']))  # noqa: E501
        if 'defense' in params:
            query_params.append(('defense', params['defense']))  # noqa: E501
        if 'conference' in params:
            query_params.append(('conference', params['conference']))  # noqa: E501
        if 'offense_conference' in params:
            query_params.append(('offenseConference', params['offense_conference']))  # noqa: E501
        if 'defense_conference' in params:
            query_params.append(('defenseConference', params['defense_conference']))  # noqa: E501
        if 'play_type' in params:
            query_params.append(('playType', params['play_type']))  # noqa: E501

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = []  # noqa: E501

        return self.api_client.call_api(
            '/plays', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='list[Play]',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)
