import json
import os
import sys
from utils import listRecursive


def remote_1(args):
    input_list = args["input"]
    site_ids = list(input_list.keys())

    file_names = list(input_list[site_ids[0]]["output_contents"].keys())
    file_headers = [
        input_list[site_ids[0]]["output_contents"][key][0]
        for key in file_names
    ]

    file_headers = dict(zip(file_names, file_headers))

    for file in file_names:
        with open(
                os.path.join(args["state"]["outputDirectory"], file + '.csv'),
                'w+') as f:
            f.writelines(['"site",', file_headers[file]])
            for site in site_ids:
                for line in input_list[site]["output_contents"][file][1:]:
                    f.writelines(['"' + site + '",', line])

    computation_output = {
        "output": "Results files sent to remote",
        "success": True
    }

    return json.dumps(computation_output)


if __name__ == '__main__':

    parsed_args = json.loads(sys.stdin.read())
    phase_key = list(listRecursive(parsed_args, 'computation_phase'))

    if 'local_1' in phase_key:
        computation_output = remote_1(parsed_args)
        sys.stdout.write(computation_output)
    else:
        raise ValueError("Error occurred at Remote")
