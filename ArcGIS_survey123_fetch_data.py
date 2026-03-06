import arcgis
from arcgis.gis import GIS
import os, re, csv

def download_survey_data(gis, survey_item_id, save_path, keep_org_item=True, store_csv_w_attachments=True, csv_fields=None):
    if csv_fields is None:
        csv_fields = ['ObjectID', 'CreationDate', 'Creator', 'EditDate', 'Plot ID',
                      'X GPS Coordinates Point 1', 'Y GPS Coordinates Point 1', 'Date and time',
                      'Surveyors name', 'Photo name 1', 'Photo name 2', 'Photo name 3',
                      'Photo name 4', 'Photo name 5', 'Attachment path']

    survey_by_id = gis.content.get(survey_item_id)

    rel_fs = survey_by_id.related_items('Survey2Service','forward')[0]
    item_excel = rel_fs.export(title=survey_by_id.title, export_format='Excel')
    item_excel.download(save_path=save_path)
    if not bool(keep_org_item):
        item_excel.delete(force=True)

    layers = rel_fs.layers + rel_fs.tables
    for i in layers:
        if i.properties.hasAttachments == True:
            feature_layer_folder = os.path.join(save_path, '{}_attachments'.format(re.sub(r'[^A-Za-z0-9]+', '', i.properties.name)))
            # Create the folder if it doesn't exist
            os.makedirs(feature_layer_folder, exist_ok=True)
            if bool(store_csv_w_attachments):
                path = os.path.join(feature_layer_folder, "{}_attachments.csv".format(i.properties.name))
            elif not bool(store_csv_w_attachments):
                path = os.path.join(save_path, "{}_attachments.csv".format(i.properties.name))
            
            with open(path, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(csv_fields)
                
                # Query all features with all fields
                features = i.query(where="1=1", out_fields='*', order_by_fields='OBJECTID ASC')
                
                for feature in features.features:
                    current_oid = feature.attributes['objectid']
                    # get info for the feature.attributes with the same name as the csv_fields

                    current_oid_attachments = i.attachments.get_list(oid=current_oid)
                
                    if len(current_oid_attachments) > 0:
                        for attachment in current_oid_attachments:
                            attachment_id = attachment['id']
                            current_attachment_path = i.attachments.download(oid=current_oid, attachment_id=attachment_id, save_path=feature_layer_folder)
                            
                            # Prepare row data with all requested fields
                            row_data = []
                            for field in csv_fields[:-1]:
                                row_data.append(feature.attributes.get(field, ''))
                                
                            # Add the attachment path as the last field
                            row_data.append(os.path.join('{}_attachments'.format(re.sub(r'[^A-Za-z0-9]+', '', i.properties.name)), 
                                                       os.path.split(current_attachment_path[0])[1]))
                            
                            csvwriter.writerow(row_data)

    print("Completed")

#example

portalURL = "https://www.arcgis.com"
username = "username"
password = "psw"
survey_item_id = "survey-ID"
save_path = rf"output_path"
keep_org_item = True
store_csv_w_attachments = True
gis = GIS(portalURL, username, password)

csv_fields = ['ObjectID', 'CreationDate', 'Creator', 'EditDate', 'Plot ID',
                      'X GPS Coordinates Point 1', 'Y GPS Coordinates Point 1', 'Date and time',
                      'Surveyors name', 'Photo name 1', 'Photo name 2', 'Photo name 3',
                      'Photo name 4', 'Photo name 5', 'Attachment path']
download_survey_data(gis, survey_item_id, save_path, keep_org_item, store_csv_w_attachments, csv_fields)