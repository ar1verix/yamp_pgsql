# -*- coding: UTF-8 -*-
import os
import argparse

from tqdm import tqdm

from yamp import parser, discriminator
from yamp.utils import remove_directory, load_file, write_json

parser_params = argparse.ArgumentParser()
parser_params.add_argument('-i', '--input', type=str, required=True)
parser_params.add_argument('-o', '--output', type=str, required=True)
parser_params.add_argument('-d', '--db', type=str, required=True)

args = parser_params.parse_args()

in_directory_path = args.input
out_directory_path = args.output
db_directory_path = args.db

in_messages_directory_path = os.path.join(in_directory_path, 'messages')
out_messages_directory_path = os.path.join(out_directory_path, 'messages')
out_structures_directory_path = os.path.join(out_directory_path, 'structures')
out_errors_directory_path = os.path.join(out_directory_path, 'errors')

remove_directory(out_directory_path)

discriminator = discriminator(db_directory_path=db_directory_path)
parser = parser(db_directory_path=db_directory_path)

errors_out_directory_path = os.path.join(out_directory_path, 'errors')
structures_out_directory_path = os.path.join(out_directory_path, 'structures')

new_directories_paths = [errors_out_directory_path, structures_out_directory_path]
new_directories_paths += [os.path.join(structures_out_directory_path, str(template.template_id)) for template in discriminator.get_templates()]
new_directories_paths += [os.path.join(structures_out_directory_path, str(discriminator.default_template_downlink.template_id))]
new_directories_paths += [os.path.join(structures_out_directory_path, str(discriminator.default_template_uplink.template_id))]
new_directories_paths += [os.path.join(structures_out_directory_path, str(discriminator.default_template_ground.template_id))]
new_directories_paths += [os.path.join(structures_out_directory_path, str(discriminator.default_template_ground_not_620.template_id))]

for new_directory_path in new_directories_paths:
    if not os.path.isdir(new_directory_path):
        os.mkdir(new_directory_path)

for in_message_file_name in tqdm(os.listdir(in_messages_directory_path)):

    in_message_body = load_file(os.path.join(in_messages_directory_path, in_message_file_name))
    discriminator_result = discriminator.identify_template(in_message_body, 16)

    if discriminator_result.code >= 0:
        if discriminator_result.code > 0:
            write_json(os.path.join(errors_out_directory_path, f'{in_message_file_name}.descriminator.json'),
                       discriminator_result.to_dict())

        template = discriminator_result.template
        parser_result = parser.parse(in_message_body, template, 16)  # code, message, structure
        if parser_result.code >= 0:
            if parser_result.code > 0:
                write_json(os.path.join(errors_out_directory_path, f'{in_message_file_name}.parser.json'),
                           parser_result.to_dict())
            original_structure_file_path = os.path.join(structures_out_directory_path,
                                                        str(template.template_id),
                                                        f'{in_message_file_name}.json')
            # Write original structure json
            write_json(original_structure_file_path, parser_result.structure)

        else:
            # If parser error
            write_json(os.path.join(errors_out_directory_path, f"{in_message_file_name}.parser.json"), parser_result.to_dict())
    else:
        # If discriminator error
        write_json(os.path.join(errors_out_directory_path, f'{in_message_file_name}.descriminator.json'), discriminator_result.to_dict())


