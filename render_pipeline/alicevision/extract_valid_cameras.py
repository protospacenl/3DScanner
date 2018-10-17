import argparse
import json
from pathlib import Path
import sys

BRACKET_PATH_POSITION_FROM_LAST = -3
SET_POSITION_FROM_LAST          = -4
SCAN_POSITION_FROM_LAST         = -5

OUTPUT_FORMAT_CSV = "{path},{scan},{set},{bracket},{ncameras},{failed},{cameras}"
OUTPUT_FORMAT_DISCOURSE = "| {path} | {scan} | {set} | {bracket} | {ncameras} | {failed} | {cameras} |"


def extractCameras(path):
    """ get name/set/bracket from path """
    sfmPathParts = path.resolve().parts
    bracket = sfmPathParts[BRACKET_PATH_POSITION_FROM_LAST]
    set = sfmPathParts[SET_POSITION_FROM_LAST]
    scan = sfmPathParts[SCAN_POSITION_FROM_LAST]
    missingCameraIDs = []

    with open(path) as sfmFile:
        sfmJson = json.load(sfmFile)

        if not sfmJson:
            print("Failed loading {0}".format(path))
            return None

        if args.output:
            output = open(Path(args.output), 'a')

        for view in sfmJson['views']:
            path = Path(view['path'])
            viewId = view['viewId']
            poseId = view['poseId']

            foundMatchingPose = False

            for pose in sfmJson['poses']:
                if pose['poseId'] == poseId:
                    foundMatchingPose = True
                    break

            if not foundMatchingPose:
                cameraId = path.stem
                if '.' in cameraId:
                    cameraId = int(cameraId.split('.')[-1]) - 100
                missingCameraIDs.append(int(cameraId))

        missingCameraIDs = sorted(missingCameraIDs)

    return scan, set, bracket, len(sfmJson['views']), missingCameraIDs


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sfm",
                        required=True,
                        help="path to cameras sfm")
    parser.add_argument("-r", "--recursive",
                        action="store_true",
                        help="recurse through path given by --sfm")
    parser.add_argument("-o", "--output",
                        help="path to output file")
    parser.add_argument("-f", "--format",
                        choices=['csv', 'discourse'],
                        default='csv',
                        help="output format")
    args = parser.parse_args()

    sfm = None
    path = Path(args.sfm)
    output = None

    if args.format == 'csv':
        outputFormat = OUTPUT_FORMAT_CSV
    elif args.format == 'discourse':
        outputFormat = OUTPUT_FORMAT_DISCOURSE
    else:
        outputFormat = OUTPUT_FORMAT_CSV

    if not path.exists():
        print("{path} does not exist!".format(path=sfmPath))
        sys.exit(1)

    if args.recursive:
        for sfmPath in sorted(path.glob('**/04_StructureFromMotion/cameras.sfm')):
            scan, set, bracket, ncameras, failed = extractCameras(sfmPath)

            print(outputFormat.format(path=sfmPath.resolve(),
                                      scan=scan,
                                      set=set,
                                      bracket=bracket,
                                      ncameras=ncameras,
                                      failed=len(failed),
                                      cameras=failed), file=output)
    else:
        scan, set, bracket, ncameras, failed = extractCameras(sfmPath)
        print(outputFormat.format(path=sfmPath.resolve(),
                                  scan=scan,
                                  set=set,
                                  bracket=bracket,
                                  ncameras=ncameras,
                                  failed=len(failed),
                                  cameras=failed), file=output)