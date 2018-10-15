import argparse
from pathlib import Path
import platform
import sys
import os

DIR_CAMERA_INIT             = "00_CameraInit"
DIR_FEATURE_EXTRACTION      = "01_FeatureExtraction"
DIR_IMAGE_MATCHING          = "02_ImageMatching"
DIR_FEATURE_MATCHING        = "03_FeatureMatching"
DIR_STRUCTURE_FROM_MOTION   = "04_StructureFromMotion"

_exe_extension = ''
if platform.system() == 'Windows':
    _file_extension = '.exe'

# below functions are based on the run_alicevision.py by
# http://filmicworlds.com/blog/command-line-photogrammetry-with-alicevision/
def Run_00_CameraInit(outPath, binPath, imgPath, cameraDbFile=""):
    dstDir = outPath / DIR_CAMERA_INIT 
    output = dstDir / "cameraInit.sfm"

    dstDir.mkdir(parents=True, exist_ok=True)

    binName = binPath / "aliceVision_cameraInit{0}".format(_file_extension)
    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --defaultFieldOfView 48.8"
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --sensorDatabase {0}".format(cameraDbFile)
    cmdLine = cmdLine + " --allowSingleView 1"
    cmdLine = cmdLine + " --imageFolder \"{0}\"".format(imgPath)
    cmdLine = cmdLine + " --output \"{0}\"".format(output)

    print(cmdLine)
    os.system(cmdLine)

    return 0


def Run_01_FeatureExtraction(outPath, binPath, numImages):
    dstDir = outPath / DIR_FEATURE_EXTRACTION
    srcSfm = outPath / DIR_CAMERA_INIT / "cameraInit.sfm"
    binName = binPath / "aliceVision_featureExtraction{0}".format(_exe_extension)

    dstDir.mkdir(parents=True, exist_ok=True)

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --describerTypes sift"
    cmdLine = cmdLine + " --forceCpuExtraction True"
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --describerPreset normal"
    cmdLine = cmdLine + " --rangeStart 0"
    cmdLine = cmdLine + " --rangeSize {0}".format(numImages)
    cmdLine = cmdLine + " --input \"{0}\"".format(srcSfm)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir)

    print(cmdLine)
    os.system(cmdLine)

    return 0


def Run_02_ImageMatching(outPath, binPath):
    dstDir = outPath / DIR_IMAGE_MATCHING
    srcSfm = outPath / DIR_CAMERA_INIT / "cameraInit.sfm"
    srcFeatures = outPath / DIR_FEATURE_EXTRACTION
    dstMatches = outPath / DIR_IMAGE_MATCHING / "imageMatches.txt"
    binName = binPath / "aliceVision_imageMatching{0}".format(_exe_extension)

    dstDir.mkdir(parents=True, exist_ok=True)

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --minNbImages 200"
    cmdLine = cmdLine + " --tree "
    cmdLine = cmdLine + " --maxDescriptors 500"
    cmdLine = cmdLine + " --verboseLevel info "
    cmdLine = cmdLine + " --weights "
    cmdLine = cmdLine + " --nbMatches 50"
    cmdLine = cmdLine + " --input \"{0}\"".format(srcSfm)
    cmdLine = cmdLine + " --featuresFolder \"{0}\"".format(srcFeatures)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstMatches)

    print(cmdLine)
    os.system(cmdLine)

    return 0


def Run_03_FeatureMatching(outPath, binPath):
    dstDir = outPath / DIR_FEATURE_MATCHING
    srcSfm = outPath / DIR_CAMERA_INIT / "cameraInit.sfm"
    srcFeatures = outPath / DIR_FEATURE_EXTRACTION
    srcImageMatches = outPath / DIR_IMAGE_MATCHING / "imageMatches.txt"
    binName = binPath / "aliceVision_featureMatching{0}".format(_exe_extension)

    dstDir.mkdir(parents=True, exist_ok=True)

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --describerTypes sift"
    cmdLine = cmdLine + " --maxMatches 0"
    cmdLine = cmdLine + " --exportDebugFiles False"
    cmdLine = cmdLine + " --savePutativeMatches False"
    cmdLine = cmdLine + " --guidedMatching False"
    cmdLine = cmdLine + " --geometricEstimator acransac"
    cmdLine = cmdLine + " --geometricFilterType fundamental_matrix"
    cmdLine = cmdLine + " --maxIteration 2048"
    cmdLine = cmdLine + " --distanceRatio 0.8"
    cmdLine = cmdLine + " --photometricMatchingMethod ANN_L2"
    cmdLine = cmdLine + " --imagePairsList \"{0}\"".format(srcImageMatches)
    cmdLine = cmdLine + " --input \"{0}\"".format(srcSfm)
    cmdLine = cmdLine + " --featuresFolders \"{0}\"".format(srcFeatures)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir)

    print(cmdLine)
    os.system(cmdLine)
    return 0


def Run_04_StructureFromMotion(outPath, binPath):
    dstDir = outPath / DIR_STRUCTURE_FROM_MOTION
    srcSfm = outPath / DIR_CAMERA_INIT / "cameraInit.sfm"
    srcFeatures = outPath / DIR_FEATURE_EXTRACTION
    srcImageMatches = outPath / DIR_IMAGE_MATCHING / "imageMatches.txt"
    srcMatches = outPath / DIR_FEATURE_MATCHING
    binName = binPath / "aliceVision_incrementalSfm{0}".format(_exe_extension)

    outputViewsAndPoses = dstDir / "cameras.sfm"
    outputBundle = dstDir / "bundle.sfm"

    dstDir.mkdir(parents=True, exist_ok=True)

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --minAngleForLandmark 2.0"
    cmdLine = cmdLine + " --minNumberOfObservationsForTriangulation 2"
    cmdLine = cmdLine + " --maxAngleInitialPair 40.0"
    cmdLine = cmdLine + " --maxNumberOfMatches 0"
    cmdLine = cmdLine + " --localizerEstimator acransac"
    cmdLine = cmdLine + " --describerTypes sift"
    cmdLine = cmdLine + " --lockScenePreviouslyReconstructed False"
    cmdLine = cmdLine + " --localBAGraphDistance 1"
    cmdLine = cmdLine + " --initialPairA "
    cmdLine = cmdLine + " --initialPairB "
    cmdLine = cmdLine + " --interFileExtension .ply"
    cmdLine = cmdLine + " --useLocalBA True"
    cmdLine = cmdLine + " --minInputTrackLength 2"
    cmdLine = cmdLine + " --useOnlyMatchesFromInputFolder False"
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --minAngleForTriangulation 3.0"
    cmdLine = cmdLine + " --maxReprojectionError 4.0"
    cmdLine = cmdLine + " --minAngleInitialPair 5.0"

    cmdLine = cmdLine + " --input \"{0}\"".format(srcSfm)
    cmdLine = cmdLine + " --featuresFolders \"{0}\"".format(srcFeatures)
    cmdLine = cmdLine + " --matchesFolders \"{0}\"".format(srcMatches)
    cmdLine = cmdLine + " --outputViewsAndPoses \"{0}\"".format(outputViewsAndPoses)
    cmdLine = cmdLine + " --extraInfoFolder \"{0}\"".format(dstDir)
    cmdLine = cmdLine + " --output \"{0}\"".format(outputBundle)

    print(cmdLine)
    os.system(cmdLine)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--bindir", dest="bindir", required=True,
                    help="path to alice binaries")
    parser.add_argument("-i", "--imagedir", dest="imgdir", required=True,
                    help="path to image")
    parser.add_argument("-o", "--output", dest="outdir", required=True,
                    help="path to output")
    parser.add_argument("-n", "--num", type=int, dest="numImages",
                    help="number of images")
    parser.add_argument("-c", "--cameradb", dest="cameradb", required=True,
                    help="path to camera db file")
    parser.add_argument("-r", "--recursive", dest="recursive", 
                    help="recurse through images path", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true",
                    help="increase output verbosity")
    args = parser.parse_args()


    binPath = Path(args.bindir)
    imgPath = Path(args.imgdir)
    outPath = Path(args.outdir)
    cameraDbPath = Path(args.cameradb)

    if not binPath.exists():
        print("{0} does not exist".format(binPath))
        sys.exit(1)

    if not imgPath.exists():
        print("{0} does not exist".format(binPath))
        sys.exit(1)


    if args.recursive:
        for path in sorted(imgPath.glob('**/')):
        	if path.stem.lower() == 'recap':
				print("Skipping recap path: {0}".format(path))
				continue
            
            numImages = len(sorted(path.glob('*.jpg')))
            
            if numImages > 0:
                fullOutputPath = outPath / path.relative_to(imgPath)
                print("***** recursing into: {0}".format(fullOutputPath))
                Run_00_CameraInit(fullOutputPath, binPath, path, cameraDbPath)
                Run_01_FeatureExtraction(fullOutputPath, binPath, numImages)
                Run_02_ImageMatching(fullOutputPath, binPath)
                Run_03_FeatureMatching(fullOutputPath, binPath)
                Run_04_StructureFromMotion(fullOutputPath, binPath)
    else:
        numImages = 0
        if args.numImages:
            numImages = args.numImages
        else:
            numImages = len(sorted(imgPath.glob('*.jpg')))

        if numImages > 0:
            Run_00_CameraInit(outPath, binPath, imgPath, cameraDbPath)
            Run_01_FeatureExtraction(outPath, binPath, numImages)
            Run_02_ImageMatching(outPath, binPath)
            Run_03_FeatureMatching(outPath, binPath)
            Run_04_StructureFromMotion(outPath, binPath)
