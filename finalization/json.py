from finalization.finalization import jsonify_data, get_all_final_data_as_dict

def create_current_final_data_selector_json():
    jsonify_data(
        get_all_final_data_as_dict(),
        '/home/brendan/PycharmProjects/Zugspitze/DataSelectors/FinalDataSelector/data'
    )
