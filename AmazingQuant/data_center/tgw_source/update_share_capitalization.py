# -*- coding: utf-8 -*-

# ------------------------------
# @Time    : 2020/5/23
# @Author  : gao
# @File    : update_share_capitalization.py
# @Project : AmazingQuant
# ------------------------------

from datetime import datetime

import pandas as pd

from AmazingQuant.constant import DatabaseName, LocalDataFolderName
from AmazingQuant.config.local_data_path import LocalDataPath
from AmazingQuant.data_center.update_local_data.save_data import save_data_to_hdf5
from AmazingQuant.data_center.api_data.get_kline import GetKlineData
from AmazingQuant.data_center.api_data.get_data import get_local_data


class UpAShareCapitalization(object):
    def __init__(self):
        self.a_share_capitalization = pd.DataFrame.empty

    def update_a_share_capitalization(self):
        """
        保存 总股本, 总市值, 流通股本, 流通市值 四个hdf5
        :return:
        """
        field_list = ['MARKET_CODE', 'EX_CHANGE_DATE', 'TOT_SHARE', 'FLOAT_SHARE', 'FLOAT_A_SHARE', 'FLOAT_B_SHARE',
                      'FLOAT_HK_SHARE']
        folder_name = LocalDataFolderName.FINANCE.value
        path = LocalDataPath.path + folder_name + '/'
        self.a_share_capitalization = get_local_data(path, 'stock_struction.h5')
        kline_object = GetKlineData()
        market_close_data = kline_object.cache_all_stock_data()['close']
        self.a_share_capitalization['EX_CHANGE_DATE'] = self.a_share_capitalization['EX_CHANGE_DATE'].astype(int)
        index = list(set(market_close_data.index).union(set(self.a_share_capitalization['EX_CHANGE_DATE'])))
        index.sort()
        share_capitalization_grouped = self.a_share_capitalization.groupby('MARKET_CODE')

        total_share = pd.DataFrame({})
        float_a_share = pd.DataFrame({})
        for i in share_capitalization_grouped:
            data = i[1].sort_values('EX_CHANGE_DATE').set_index('EX_CHANGE_DATE')
            # print(data['TOT_SHARE'])
            try:
                total_share[i[0]] = data['TOT_SHARE'].reindex(index)
                float_a_share[i[0]] = data['FLOAT_A_SHARE'].reindex(index)
            except ValueError:
                # 有四只票 change date 重复, 需要手工清洗修正
                # print(data[data.index.duplicated()])
                total_share[i[0]] = data[data.index.duplicated()]['TOT_SHARE'].reindex(index)
                float_a_share[i[0]] = data[data.index.duplicated()]['FLOAT_A_SHARE'].reindex(index)
        total_share = total_share.fillna(method='ffill').reindex(market_close_data.index)
        float_a_share = float_a_share.fillna(method='ffill').reindex(market_close_data.index)
        total_share_value = total_share.multiply(10000) * market_close_data
        float_a_share_value = float_a_share.multiply(10000) * market_close_data

        folder_name = LocalDataFolderName.INDICATOR_EVERYDAY.value
        path = LocalDataPath.path + folder_name + '/'
        save_data_to_hdf5(path, 'total_share', total_share)
        save_data_to_hdf5(path, 'float_a_share', float_a_share)
        save_data_to_hdf5(path, 'total_share_value', total_share_value)
        save_data_to_hdf5(path, 'float_a_share_value', float_a_share_value)


if __name__ == '__main__':
    share_capitalization_obj = UpAShareCapitalization()
    share_capitalization_obj.update_a_share_capitalization()
