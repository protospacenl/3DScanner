import argparse
from pathlib import Path
import platform
import sys
import os
from math import floor

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
    binName = binPath /  "aliceVision_cameraConnection{0}".format(_exe_extension)

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


    #cmd = "aliceVision_depthMapEstimation  --sgmGammaC 5.5 --sgmWSH 4 --refineGammaP 8.0 --refineSigma 15 --refineNSamplesHalf 150 --sgmMaxTCams 10 --refineWSH 3 --downscale 2 --refineMaxTCams 6 --verboseLevel info --refineGammaC 15.5 --sgmGammaP 8.0 --ini \"c:/users/geforce/appdata/local/temp/MeshroomCache/PrepareDenseScene/4f0d6d9f9d072ed05337fd7c670811b1daa00e62/mvs.ini\" --refineNiters 100 --refineNDepthsToRefine 31 --refineUseTcOrRcPixSize False --output \"c:/users/geforce/appdata/local/temp/MeshroomCache/DepthMap/18f3bd0a90931bd749b5eda20c8bf9f6dab63af9\" --rangeStart 0 --rangeSize 3"
    #cmd = binName + " --sgmGammaC 5.5 --sgmWSH 4 --refineGammaP 8.0 --refineSigma 15 --refineNSamplesHalf 150 --sgmMaxTCams 10 --refineWSH 3 --downscale 2 --refineMaxTCams 6 --verboseLevel info --refineGammaC 15.5 --sgmGammaP 8.0 --ini \"c:/users/geforce/appdata/local/temp/MeshroomCache/PrepareDenseScene/4f0d6d9f9d072ed05337fd7c670811b1daa00e62/mvs.ini\" --refineNiters 100 --refineNDepthsToRefine 31 --refineUseTcOrRcPixSize False --output \"build_files/07_DepthMap/\" --rangeStart 0 --rangeSize 3"
    #cmd = binName + " --sgmGammaC 5.5 --sgmWSH 4 --refineGammaP 8.0 --refineSigma 15 --refineNSamplesHalf 150 --sgmMaxTCams 10 --refineWSH 3 --downscale 2 --refineMaxTCams 6 --verboseLevel info --refineGammaC 15.5 --sgmGammaP 8.0 --ini \"" + srcIni + "\" --refineNiters 100 --refineNDepthsToRefine 31 --refineUseTcOrRcPixSize False --output \"build_files/07_DepthMap/\" --rangeStart 0 --rangeSize 3"
    #print(cmd)
    #os.system(cmd)

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
    parser.add_argument("-d", "--depthmap", dest="do_depthmap", 
                    help="generate depth map", action="store_true")
    parser.add_argument("-m", "--meshing", dest="do_meshing", 
                    help="generate mesh, implies -d", action="store_true")
    parser.add_argument("-t", "--texturing", dest="do_texturing", 
                    help="add texture, implies -d and -m", action="store_true")
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
                if args.do_depthmap or args.do_meshing or args.do_texturing:
                    Run_05_PrepareDenseScene(fullOutputPath, binPath)
                    Run_06_CameraConnection(fullOutputPath, binPath)
                    Run_07_DepthMap(fullOutputPath, binPath, numImages, 3)
                    Run_08_DepthMapFilter(fullOutputPath, binPath)

                    if args.do_meshing or args.do_texturing:
                        Run_09_Meshing(fullOutputPath, binPath)
                        Run_10_MeshFiltering(fullOutputPath, binPath)

                        if args.do_texturing:
                            Run_11_Texturing(fullOutputPath, binPath)
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
            if args.do_depthmap or args.do_meshing or args.do_texturing:
                Run_05_PrepareDenseScene(outPath, binPath)
                Run_06_CameraConnection(outPath, binPath)
                Run_07_DepthMap(outPath, binPath, numImages, 3)
                Run_08_DepthMapFilter(outPath, binPath)

                if args.do_meshing or args.do_texturing:
                    Run_09_Meshing(outPath, binPath)
                    Run_10_MeshFiltering(outPath, binPath)

                    if args.do_texturing:
                        Run_11_Texturing(outPath, binPath)
