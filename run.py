import json
import os
import csv
import argparse

def sort_tracks(tracks_list, mappings):
    tracks_order = [(v[0], v[2]) for v in mappings.values()]
    tracks_order = [x[1] for x in sorted(tracks_order, key=lambda x: int(x[0]))]
    tracks_list = sorted(tracks_list, key=lambda x: tracks_order.index(x['name']))
    return tracks_list


def inspect_filename(filename):
    _, file_extension = os.path.splitext(filename)
    file_extension = file_extension[1:]

    if file_extension == "bw":
        file_format = "bigwig"
        track_type = "wig"
    elif file_extension == "bam":
        file_format = "bam"
        track_type = "alignment"
    else:
        # TODO: support other data types!
        raise ValueError(f"Unknown file extension: {file_extension}")
    return (file_format, track_type)


def get_tracks_array(folder, mappings, genome):
    o = []
    cwd = os.getcwd()
    os.chdir(folder)
    for root, directories, files in os.walk('.'):
        for file in files:
            if file in mappings.keys():
                file_format, track_type = inspect_filename(file)
                track = {
                    'sourceType': 'file',
                    'name': mappings[file][2],
                    'color': mappings[file][3],
                    'url': os.path.join("data", root, file),
                    'description': file,
                    'genome': genome,
                    'format': file_format,
                    'type': track_type
                }
                o.append(track)
    os.chdir(cwd)
    o = sort_tracks(o, mappings)
    return o


def import_mapping(mapping_path):
    mapping = {}
    with open(mapping_path) as csvfile:
        reader = csv.reader(csvfile, delimiter=',',quotechar=None)
        for row in reader:
            key = row[1]
            mapping[key] = row
    return mapping


def main():

    parser = argparse.ArgumentParser(description='A tool to generate HPCIGV config file and start a singularity instance.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('data-path',
                        help = 'Target data folder')
    parser.add_argument('--mapping-file', type=str,
                        default = "custom/mapping.txt",
                        help = 'Path to a mapping file (see docs)')
    parser.add_argument('--template',
                        default = "igvwebConfig_template.json",
                        help = 'Path to template igvwebConfig json file')
    parser.add_argument('--genome',
                        default = "mm10",
                        help='Genome string')
    parser.add_argument('--output',
                        default = "custom/igvwebConfig.js",
                        help='Path to igvwebConfig output file')
    parser.add_argument('--port',
                        default = "8898",
                        help = 'TCP port to bind HPCIGV to.')

    args = parser.parse_args()
    data_path = vars(args)["data-path"]


    mappings = import_mapping(args.mapping_file)
    igvwebconfig = json.load(open(args.template))
    tracks = get_tracks_array(data_path, mappings, args.genome)
    igvwebconfig["igvConfig"]["genome"] = args.genome

    for track in tracks:
        igvwebconfig["igvConfig"]["tracks"].append(track)

    with open(args.output, "w") as fout:
        fout.write("var igvwebConfig = {}".format(json.dumps(igvwebconfig)))


    os.system(f"singularity exec --bind custom:/igv-webapp/dist/custom --bind {data_path}:/igv-webapp/dist/data --bind {args.output}:/igv-webapp/dist/igvwebConfig.js hpcigv.sif npx http-server --port {args.port} /igv-webapp/dist")


if __name__ == '__main__':
    main()
