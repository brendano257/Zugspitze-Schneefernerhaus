from finalization.runtime import jsonify_data, get_all_final_data_as_dicts


def create_current_final_data_selector_json():
    jsonify_data(
        get_all_final_data_as_dicts()[0],
        '/home/brendan/PycharmProjects/Zugspitze/DataSelectors/FinalDataSelector/data'
    )
