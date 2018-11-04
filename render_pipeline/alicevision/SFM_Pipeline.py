import argparse
from pathlib import Path
import json
import shutil
import platform
import subprocess
import sys
import os
from math import floor

BRACKET_PATH_POSITION_FROM_LAST = -1
SET_POSITION_FROM_LAST          = -2
SCAN_POSITION_FROM_LAST         = -3

DIR_CAMERA_INIT             = "00_CameraInit"
DIR_FEATURE_EXTRACTION      = "01_FeatureExtraction"
DIR_IMAGE_MATCHING          = "02_ImageMatching"
DIR_FEATURE_MATCHING        = "03_FeatureMatching"
DIR_STRUCTURE_FROM_MOTION   = "04_StructureFromMotion"
DIR_PREPARE_DENSE_SCENE     = "05_PrepareDenseScene"
DIR_CAMERA_CONNECTION       = "06_CameraConnection"
DIR_DEPTH_MAP               = "07_DepthMap"
DIR_DEPTH_MAP_FILTER        = "08_DepthMapFilter"
DIR_MESHING                 = "09_Meshing"
DIR_MESH_FILTERING          = "10_MeshFiltering"
DIR_TEXTURING               = "11_Texturing"
DIR_EXPORT_KEYPOINTS        = "exp_keypoints"
DIR_EXPORT_MATCHES          = "exp_matches"

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

    if output.exists():

        sfmJson = None

        with open(output) as sfmFile:
            sfmJson = json.load(sfmFile)

        if not sfmJson:
            print("Failed loading {0}".format(output))
            return 0
        for view in sfmJson['views']:
            path = Path(view['path'])

            cameraId = path.stem
            if '.' in cameraId:
                cameraId = int(cameraId.split('.')[-1]) - 100
            view['viewId'] = cameraId

        with open(output, 'wt') as sfmFile:
            json.dump(sfmJson, sfmFile, indent=4)

    return 0


def Run_01_FeatureExtraction(outPath, binPath, numImages, ultra=False):
    dstDir = outPath / DIR_FEATURE_EXTRACTION
    srcSfm = outPath / DIR_CAMERA_INIT / "cameraInit.sfm"
    binName = binPath / "aliceVision_featureExtraction{0}".format(_exe_extension)

    dstDir.mkdir(parents=True, exist_ok=True)

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --describerTypes sift"
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --rangeStart 0"
    cmdLine = cmdLine + " --rangeSize {0}".format(numImages)
    cmdLine = cmdLine + " --input \"{0}\"".format(srcSfm)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir)

    if ultra:
        cmdLine = cmdLine + " --describerPreset ultra"

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


def Run_05_PrepareDenseScene(outPath, binPath):
    dstDir = outPath / DIR_PREPARE_DENSE_SCENE
    srcSfm = outPath / DIR_STRUCTURE_FROM_MOTION / "bundle.sfm"
    binName = binPath / "aliceVision_prepareDenseScene{0}".format(_exe_extension)

    dstDir.mkdir(parents=True, exist_ok=True)

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --input \"{0}\"".format(srcSfm)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir)

    print(cmdLine)
    os.system(cmdLine)
    return 0


def Run_06_CameraConnection(outPath, binPath):
    dstDir = outPath / DIR_CAMERA_CONNECTION
    dstDir.mkdir(parents=True, exist_ok=True)

    srcIni = outPath / DIR_PREPARE_DENSE_SCENE / "mvs.ini"

    # This step kindof breaks the directory structure. Tt creates
    # a camsPairsMatrixFromSeeds.bin file in in the same file as mvs.ini
    binName = binPath / "aliceVision_cameraConnection{0}".format(_exe_extension)

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --ini \"{0}\"".format(srcIni)

    print(cmdLine)
    os.system(cmdLine)
    return 0


def Run_07_DepthMap(outPath, binPath, numImages, groupSize):
    dstDir = outPath / DIR_DEPTH_MAP
    dstDir.mkdir(parents=True, exist_ok=True)

    numGroups = floor((numImages + (groupSize - 1)) / groupSize)

    srcIni = outPath / DIR_PREPARE_DENSE_SCENE / "mvs.ini"
    binName = binPath / "aliceVision_depthMapEstimation{0}".format(_exe_extension)

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --sgmGammaC 5.5"
    cmdLine = cmdLine + " --sgmWSH 4"
    cmdLine = cmdLine + " --refineGammaP 8.0"
    cmdLine = cmdLine + " --refineSigma 15"
    cmdLine = cmdLine + " --refineNSamplesHalf 150"
    cmdLine = cmdLine + " --sgmMaxTCams 10"
    cmdLine = cmdLine + " --refineWSH 3"
    cmdLine = cmdLine + " --downscale 2"
    cmdLine = cmdLine + " --refineMaxTCams 6"
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --refineGammaC 15.5"
    cmdLine = cmdLine + " --sgmGammaP 8.0"
    cmdLine = cmdLine + " --refineNiters 100"
    cmdLine = cmdLine + " --refineNDepthsToRefine 31"
    cmdLine = cmdLine + " --refineUseTcOrRcPixSize False"
    cmdLine = cmdLine + " --ini \"{0}\"".format(srcIni)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir)

    for groupIter in range(numGroups):
        groupStart = groupSize * groupIter
        groupSize = min(groupSize, numImages - groupStart)
        print("DepthMap Group %d/%d: %d, %d" % (groupIter, numGroups, groupStart, groupSize))

        cmd = cmdLine + " --rangeStart {start} --rangeSize {size}".format(start=groupStart, size=groupSize)
        print(cmd)
        os.system(cmd)

    return 0


def Run_08_DepthMapFilter(outPath, binPath):
    dstDir = outPath / DIR_DEPTH_MAP_FILTER
    dstDir.mkdir(parents=True, exist_ok=True)

    binName = binPath / "aliceVision_depthMapFiltering{0}".format(_exe_extension)
    srcIni = outPath / DIR_PREPARE_DENSE_SCENE / "mvs.ini"
    srcDepthDir = outPath / DIR_DEPTH_MAP

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --minNumOfConsistensCamsWithLowSimilarity 4"
    cmdLine = cmdLine + " --minNumOfConsistensCams 3"
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --pixSizeBall 0"
    cmdLine = cmdLine + " --pixSizeBallWithLowSimilarity 0"
    cmdLine = cmdLine + " --nNearestCams 10"
    cmdLine = cmdLine + " --ini \"{0}\"".format(srcIni)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir)
    cmdLine = cmdLine + " --depthMapFolder \"{0}\"".format(srcDepthDir)

    print(cmdLine)
    os.system(cmdLine)
    return 0


def Run_09_Meshing(outPath, binPath):
    dstDir = outPath / DIR_MESHING
    dstDir.mkdir(parents=True, exist_ok=True)

    binName = binPath / "aliceVision_meshing{0}".format(_exe_extension)
    srcIni = outPath / DIR_PREPARE_DENSE_SCENE / "mvs.ini"
    srcDepthFilterDir = outPath / DIR_DEPTH_MAP_FILTER
    srcDepthMapDir = outPath / DIR_DEPTH_MAP

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --simGaussianSizeInit 10.0"
    cmdLine = cmdLine + " --maxInputPoints 50000000"
    cmdLine = cmdLine + " --repartition multiResolution"
    cmdLine = cmdLine + " --simGaussianSize 10.0"
    cmdLine = cmdLine + " --simFactor 15.0"
    cmdLine = cmdLine + " --voteMarginFactor 4.0"
    cmdLine = cmdLine + " --contributeMarginFactor 2.0"
    cmdLine = cmdLine + " --minStep 2"
    cmdLine = cmdLine + " --pixSizeMarginFinalCoef 4.0"
    cmdLine = cmdLine + " --maxPoints 5000000"
    cmdLine = cmdLine + " --maxPointsPerVoxel 1000000"
    cmdLine = cmdLine + " --angleFactor 15.0"
    cmdLine = cmdLine + " --partitioning singleBlock"
    cmdLine = cmdLine + " --minAngleThreshold 1.0"
    cmdLine = cmdLine + " --pixSizeMarginInitCoef 2.0"
    cmdLine = cmdLine + " --refineFuse True"
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --ini \"{0}\"".format(srcIni)
    cmdLine = cmdLine + " --depthMapFilterFolder \"{0}\"".format(srcDepthFilterDir)
    cmdLine = cmdLine + " --depthMapFolder \"{0}\"".format(srcDepthMapDir)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir / "mesh.obj")

    print(cmdLine)
    os.system(cmdLine)
    return 0


def Run_10_MeshFiltering(outPath, binPath):
    dstDir = outPath / DIR_MESH_FILTERING
    dstDir.mkdir(parents=True, exist_ok=True)

    binName = binPath / "aliceVision_meshFiltering{0}".format(_exe_extension)

    srcMesh = outPath / DIR_MESHING / "mesh.obj"
    dstMesh = outPath / DIR_MESH_FILTERING / "mesh.obj"

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --removeLargeTrianglesFactor 60.0"
    cmdLine = cmdLine + " --iterations 5"
    cmdLine = cmdLine + " --keepLargestMeshOnly True"
    cmdLine = cmdLine + " --lambda 1.0"
    cmdLine = cmdLine + " --input \"{0}\"".format(srcMesh)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstMesh)

    print(cmdLine)
    os.system(cmdLine)
    return 0


def Run_11_Texturing(outPath, binPath):
    dstDir = outPath / DIR_TEXTURING
    dstDir.mkdir(parents=True, exist_ok=True)

    binName = binPath / "aliceVision_texturing{0}".format(_exe_extension)

    srcMesh = outPath / DIR_MESH_FILTERING / "mesh.obj"
    srcRecon = outPath / DIR_MESHING / "denseReconstruction.bin"
    srcIni = outPath / DIR_PREPARE_DENSE_SCENE / "mvs.ini"

    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --textureSide 8192"
    cmdLine = cmdLine + " --downscale 2"
    cmdLine = cmdLine + " --verboseLevel info"
    cmdLine = cmdLine + " --padding 15"
    cmdLine = cmdLine + " --unwrapMethod Basic"
    cmdLine = cmdLine + " --outputTextureFileType png"
    cmdLine = cmdLine + " --flipNormals False"
    cmdLine = cmdLine + " --fillHoles False"
    cmdLine = cmdLine + " --inputDenseReconstruction \"{0}\"".format(srcRecon)
    cmdLine = cmdLine + " --inputMesh \"{0}\"".format(srcMesh)
    cmdLine = cmdLine + " --ini \"{0}\"".format(srcIni)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir)

    print(cmdLine)
    os.system(cmdLine)

    return 0


def Run_exportKeypoints(outPath, binPath):
    dstDir = outPath / DIR_EXPORT_KEYPOINTS

    srcSfm = outPath / DIR_STRUCTURE_FROM_MOTION / "bundle.sfm"
    srcFeatures = outPath / DIR_FEATURE_EXTRACTION

    dstDir.mkdir(parents=True, exist_ok=True)

    binName = binPath / "aliceVision_exportKeypoints{0}".format(_file_extension)
    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --input \"{0}\"".format(srcSfm)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir)
    cmdLine = cmdLine + " --featuresFolders \"{0}\"".format(srcFeatures)
    cmdLine = cmdLine + " --verboseLevel info"

    print(cmdLine)
    os.system(cmdLine)

    return 0


def Run_exportMatches(outPath, binPath):
    dstDir = outPath / DIR_EXPORT_MATCHES

    srcSfm = outPath / DIR_STRUCTURE_FROM_MOTION / "bundle.sfm"
    srcFeatures = outPath / DIR_FEATURE_EXTRACTION
    srcMatches = outPath / DIR_FEATURE_MATCHING

    dstDir.mkdir(parents=True, exist_ok=True)

    binName = binPath / "aliceVision_exportMatches{0}".format(_file_extension)
    cmdLine = "{0}".format(binName)
    cmdLine = cmdLine + " --input \"{0}\"".format(srcSfm)
    cmdLine = cmdLine + " --output \"{0}\"".format(dstDir)
    cmdLine = cmdLine + " --featuresFolders \"{0}\"".format(srcFeatures)
    cmdLine = cmdLine + " --matchesFolders \"{0}\"".format(srcMatches)
    cmdLine = cmdLine + " --verboseLevel info"

    print(cmdLine)
    os.system(cmdLine)

    return 0


def convert_svg_to_png(from_path):
    for file in sorted(from_path.glob('*.svg')):

        cmd_list = ["{0}".format(Path('C:\\Program Files\\Inkscape\\inkscape.exe')), '-z',
                    '--export-png', "{0}".format(file.with_suffix('.png')),
                    '--export-width', "640",
                    "{0}".format(file)]

        # Invoke the command.  Divert output that normally goes to stdout or stderr.
        p = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Below, < out > and < err > are strings or < None >, derived from stdout and stderr.
        out, err = p.communicate()      # Waits for process to terminate

        if p.returncode:
            raise Exception('Inkscape error: ' + (err or '?'))


def copy_files(from_path, to_path):
    if not from_path.exists():
        return

    to_path.mkdir(parents=True, exist_ok=True)

    for file in sorted(from_path.glob('*')):
        print("copying file: {fromPath} -> {toPath}".format(fromPath=file, toPath=to_path))
        try:
            shutil.copy(file.as_posix(), (to_path / file.name).as_posix())
        except shutil.Error as e:
            print('Could not copy file. Error: %s' % e)
        except OSError as e:
            print('Could not copy file. Error: %s' % e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--bindir", dest="bindir", required=True,
                        help="path to alice binaries")
    parser.add_argument("-i", "--imagedir", dest="imgdir", required=True,
                        help="path to image")
    parser.add_argument("-o", "--output", dest="outdir", required=True,
                        help="path to output")
    parser.add_argument("-c", "--cameradb", dest="cameradb", required=True,
                        help="path to camera db file")
    parser.add_argument("--resultPath",
                        help="path to export results to")
    parser.add_argument("-u", "--ultra", action="store_true",
                        help="set describer preset to ultra")
    parser.add_argument("--structureFromMotion", dest="doStructureFromMotion", action="store_true",
                        help="export keypoints")
    parser.add_argument("--exportKeypoints", dest="doExportKeypoints", action="store_true",
                        help="export keypoints")
    parser.add_argument("--exportMatches", dest="doExportMatches", action="store_true",
                        help="export matches")
    parser.add_argument("-d", "--depthmap", dest="doGenerateDepthMap",
                        help="generate depth map", action="store_true")
    parser.add_argument("-m", "--meshing", dest="doGenerateMesh",
                        help="generate mesh, implies -d", action="store_true")
    parser.add_argument("-t", "--texturing", dest="doApplyTexture",
                        help="add texture, implies -d and -m", action="store_true")
    parser.add_argument("--pathParts", type=int, default=3,
                        help="use last n path parts to construct result output name")
    parser.add_argument("--svg2png", dest="doSvg2Png",
                        help="convert svg to png", action="store_true")
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

    if args.doStructureFromMotion and not imgPath.exists():
        print("{0} does not exist".format(binPath))
        sys.exit(1)

    for path in sorted(imgPath.glob('**/br*')):
        if path.stem.lower() == 'recap':
            print("Skipping recap path: {0}".format(path))
            continue

        numImages = len(sorted(path.glob('*.jpg')))

        if numImages > 0:
            fullOutputPath = outPath / path.relative_to(imgPath)
            resultPath = None

            if args.resultPath is not None:
                resultPath = Path(args.resultPath) / '/'.join(fullOutputPath.parts[-args.pathParts:])

            print("**** Image path: {0}".format(path))
            print("**** Output path: {0}".format(fullOutputPath))
            print("**** Result path: {0}".format(resultPath))

            if args.doStructureFromMotion:
                Run_00_CameraInit(fullOutputPath, binPath, path, cameraDbPath)
                Run_01_FeatureExtraction(fullOutputPath, binPath, numImages, ultra=args.ultra)
                Run_02_ImageMatching(fullOutputPath, binPath)
                Run_03_FeatureMatching(fullOutputPath, binPath)
                Run_04_StructureFromMotion(fullOutputPath, binPath)

            if args.doExportKeypoints and (fullOutputPath / DIR_STRUCTURE_FROM_MOTION).exists():
                Run_exportKeypoints(fullOutputPath, binPath)

                keypointsPath = fullOutputPath / DIR_EXPORT_KEYPOINTS
                if keypointsPath.exists():
                    if args.doSvg2Png:
                        convert_svg_to_png(keypointsPath)

                    if resultPath is not None:
                        copy_files(keypointsPath, resultPath / DIR_EXPORT_KEYPOINTS)

            if args.doExportMatches and (fullOutputPath / DIR_STRUCTURE_FROM_MOTION).exists():
                Run_exportMatches(fullOutputPath, binPath)

                matchesPath = fullOutputPath / DIR_EXPORT_MATCHES
                if matchesPath.exists():
                    if args.doSvg2Png:
                        convert_svg_to_png(matchesPath)

                    if resultPath is not None:
                        copy_files(fullOutputPath / DIR_EXPORT_MATCHES, resultPath / DIR_EXPORT_MATCHES)

            if args.doGenerateDepthMap or args.doGenerateMesh or args.doApplyTexture:
                Run_05_PrepareDenseScene(fullOutputPath, binPath)
                Run_06_CameraConnection(fullOutputPath, binPath)
                Run_07_DepthMap(fullOutputPath, binPath, numImages, 3)
                Run_08_DepthMapFilter(fullOutputPath, binPath)

                if args.doGenerateMesh or args.doApplyTexture:
                    Run_09_Meshing(fullOutputPath, binPath)
                    Run_10_MeshFiltering(fullOutputPath, binPath)

                    if args.doApplyTexture:
                        Run_11_Texturing(fullOutputPath, binPath)

                        if (fullOutputPath / DIR_TEXTURING).exists() and resultPath is not None:
                            copy_files(fullOutputPath / DIR_TEXTURING, resultPath / DIR_TEXTURING)
