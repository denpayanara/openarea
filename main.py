if len(list_nara) != 0:

    # 開局エリアのポリゴン作成

    print('開局エリアのポリゴンを作成します...')

    gdf_area_0 = gpd.read_file('A002005212020DDSWC29.geojson').fillna('')

    df_nara = pd.DataFrame(list_nara)

    gdf_area_1 = gpd.GeoDataFrame()

    for index, row in df_nara.iterrows():

        # print(row['addr'])

        merge_data = pd.merge(gdf_area_0[gdf_area_0['addr'].str.contains(row['addr'])].reset_index(drop=True), df_nara, on='addr')

        gdf_area_1 = pd.concat([gdf_area_1, merge_data])

    # 同一地域の融合
    # 4Gと5Gは同一のID

    gdf_dissolve = gdf_area_1.dissolve(by=['ID', 'Type', 'Date'], as_index=False)

    # gdf_dissolve.columns

    gdf_area_2 = gdf_dissolve[['ID', 'Date', 'Type', 'PostalCode', 'Prefecture', 'City', 'addr', 'geometry']]

    gdf_area_2.to_file('data/開局エリア.geojson', driver='GeoJSON', index=False)
