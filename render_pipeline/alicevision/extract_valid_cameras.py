import argparse
import json
from pathlib import Path
import sys


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--sfm",
                        dest="sfm",
                        required=True,
                        help="path to cameras sfm")
    parser.add_argument("-o", "--output",
                        dest="output",
                        help="path to output file")
    args = parser.parse_args()

    sfm = None
    output = None
    sfmPath = Path(args.sfm)

    if args.output:
        output = open(Path(args.output), 'a')

    with open(sfmPath) as sfmfile:
        sfm = json.load(sfmfile)

    if not sfm:
        print("Failed loading {0}".format(sfmPath))
        sys.exit(2)

    missingCameraIDs = []
    for view in sfm['views']:
        path = Path(view['path'])
        viewId = view['viewId']
        poseId = view['poseId']
        foundMatchingPose = False

        for pose in sfm['poses']:
            if pose['poseId'] == poseId:
                foundMatchingPose = True
                break

        if not foundMatchingPose:
            cameraId = path.stem
            if '.' in cameraId:
                cameraId = int(cameraId.split('.')[-1]) - 100
            missingCameraIDs.append(int(cameraId))

    missingCameraIDs = sorted(missingCameraIDs)

    print("{0}: {1}".format(sfmPath.absolute(), missingCameraIDs), file=output)

