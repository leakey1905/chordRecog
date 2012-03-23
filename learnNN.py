import numpy as np
from itertools import izip
import neuralnet as nn
import activation as act

def learnNNbuff(chromaNorm = 'L1', constantQNorm = 'Linf', deltaTrain = 2, nnStruct = [256, 150, 24], errorFunc = 'SSE', verbose = False):
    '''
    Learns neural network weights with buffered feature input (batch training in segments). 
    Use this function when thrashing to disk is a possibility

    PARAMETERS
    ----------
    chromaNorm: L1, L2, Linf, or None, normalization of chroma
    constantQNorm: L1, L2, Linf, or None, normalization of constant q transform
    deltaTrain {int}: how many songs to train after. Buffering features prevents thrashing to disk.
    nnStruct {List}: neural network layer list (each element is number of neurons at the layer
    errorFunc {String}: 'KLDiv' or 'SSE'
    verbose {Boolean}: report progress to standard out

    RETURN
    ------
    net: trained neural network
    '''

    # initialize feature storage
    Xtrain = []     # Constant-Q transform
    Xtarget = []    # Bass and treble chromagram

    # Set up neural network
    # uses sigmoid activation function by default at each layer
    # output activation depends on the type of chromaNorm specified
    activations = [act.Sigmoid()] * (len(nnStruct)-2)
    if chromaNorm == 'L1':
        # partitioned SoftMax output (L1 normalization for each chromagram)
        activations.append(act.SoftMax([12]))
    elif chromaNorm == 'L2':
        activations.append(act.Identity())
    elif chromaNorm == 'Linf':
        activations.append(act.Sigmoid())
    else:
        activations.append(act.Identity())

    # Instantiate neural network
    # assumes full connectivity between layer neurons.
    net = nn.NeuralNet(nnStruct, actFunc=activations)

    # read constant-q transform preliminary features
    qFile = open('data/logfreqspec.csv', 'r')
    # read bass and treble chromagram features
    cFile = open('data/bothchroma.csv', 'r')

    songNum = 0
    for cObs, qObs in izip(cFile, qFile):
        cObs = cObs.split(",")
        qObs = qObs.split(",")
        
        # check if we have moved to a new song
        if cObs[0]:
            # check features are in sync by audio file path
            if not qObs[0] or cObs[0] != qObs[0]:
                raise ValueError("Feature files out of sync")
            
            songNum += 1
            if verbose:
                print "Processing song: ", cObs[0]

        # train the neural net with buffered features
        if songNum % deltaTrain == 0:
            trainNet(np.asarray(Xtrain), np.asarray(Xtarget), net, errorFunc, verbose)
            # clear feature buffers
            del Xtrain[:]
            del Xtarget[:]

        # double check features are in sync by timestamp
        if float(cObs[1]) != float(qObs[1]):
            raise ValueError("Feature files out of sync")
        
        # get Constant-Q transform
        constantQ = np.asfarray(qObs[2:])
        
        # perform feature normalization
        if np.sum(constantQ) != 0:
            if constantQNorm == 'L1':
                constantQ /= np.sum(np.abs(constantQ))
            elif constantQNorm == 'L2':
                constantQ /= np.sum(constantQ ** 2)
            elif constantQNorm == 'Linf':
                constantQ /= np.max(np.abs(constantQ))

        Xtrain.append(constantQ)

        # get chromagrams
        chroma = np.asfarray(cObs[2:])

        # perform feature normalization
        if chromaNorm == 'L1':
            if np.sum(chroma[0:12]) != 0:
                chroma[0:12] /= np.sum(np.abs(chroma[0:12]))
            if np.sum(chroma[12:24]) != 0:
                chroma[12:24] /= np.sum(np.abs(chroma[12:24]))
        elif chromaNorm == 'L2':
            if np.sum(chroma[0:12]) != 0:
                chroma[0:12] /= np.sum(chroma[0:12] ** 2)
            if np.sum(chroma[12:24]) != 0:
                chroma[12:24] /= np.sum(chroma[12:24] ** 2)
        elif chromaNorm == 'Linf':
            if np.sum(chroma[0:12]) != 0:
                chroma[0:12] /= np.max(np.abs(chroma[0:12]))
            if np.sum(chroma[12:24]) != 0:
                chroma[12:24] /= np.max(np.abs(chroma[12:24]))

        Xtarget.append(chroma)

    # train leftovers (< deltaTrain songs)
    trainNet(np.asarray(Xtrain), np.asarray(Xtarget), net, errorFunc, verbose)

    if verbose:
        print "Done training neural network."

    qFile.close()
    cFile.close()

    return net

def learnNN(chromaNorm = 'L1', constantQNorm = 'Linf', deltaTrain = 2, nnStruct = [256, 50, 24], errorFunc = 'SSE', verbose = False):
    '''
    Learns neural network weights with unbuffered feature input: store all features in main memory and do one giant batch train.

    PARAMETERS
    ----------
    chromaNorm: L1, L2, Linf, or None, normalization of chroma
    constantQNorm: L1, L2, Linf, or None, normalization of constant q transform
    nnStruct {List}: neural network layer list (each element is number of neurons at the layer
    errorFunc {String}: 'KLDiv' or 'SSE'
    verbose {Boolean}: report progress to standard out

    RETURN
    ------
    net: trained neural network
    '''

    # initialize feature storage
    Xtrain = []     # Constant-Q transform
    Xtarget = []    # Bass and treble chromagram

    # Set up neural network
    # uses sigmoid activation function by default at each layer
    # output activation depends on the type of chromaNorm specified
    activations = [act.Sigmoid()] * (len(nnStruct)-2)
    if chromaNorm == 'L1':
        # partitioned SoftMax output (L1 normalization for each chromagram)
        activations.append(act.SoftMax([12]))
    elif chromaNorm == 'L2':
        activations.append(act.Identity())
    elif chromaNorm == 'Linf':
        activations.append(act.Sigmoid())
    else:
        activations.append(act.Identity())

    # Instantiate neural network
    # assumes full connectivity between layer neurons.
    net = nn.NeuralNet(nnStruct, actFunc=activations)

    # read constant-q transform preliminary features
    qFile = open('data/logfreqspec.csv', 'r')
    # read bass and treble chromagram features
    cFile = open('data/bothchroma.csv', 'r')

    for cObs, qObs in izip(cFile, qFile):
        cObs = cObs.split(",")
        qObs = qObs.split(",")
        
        # check if we have moved to a new song
        if cObs[0]:
            # check features are in sync by audio file path
            if not qObs[0] or cObs[0] != qObs[0]:
                raise ValueError("Feature files out of sync")
            
            if verbose:
                print "Processing song: ", cObs[0]

        # double check features are in sync by timestamp
        if float(cObs[1]) != float(qObs[1]):
            raise ValueError("Feature files out of sync")
        
        # get Constant-Q transform
        constantQ = np.asfarray(qObs[2:])
        
        # perform feature normalization
        if np.sum(constantQ) != 0:
            if constantQNorm == 'L1':
                constantQ /= np.sum(np.abs(constantQ))
            elif constantQNorm == 'L2':
                constantQ /= np.sum(constantQ ** 2)
            elif constantQNorm == 'Linf':
                constantQ /= np.max(np.abs(constantQ))

        Xtrain.append(constantQ)

        # get chromagrams
        chroma = np.asfarray(cObs[2:])

        # perform feature normalization
        if chromaNorm == 'L1':
            if np.sum(chroma[0:12]) != 0:
                chroma[0:12] /= np.sum(np.abs(chroma[0:12]))
            if np.sum(chroma[12:24]) != 0:
                chroma[12:24] /= np.sum(np.abs(chroma[12:24]))
        elif chromaNorm == 'L2':
            if np.sum(chroma[0:12]) != 0:
                chroma[0:12] /= np.sum(chroma[0:12] ** 2)
            if np.sum(chroma[12:24]) != 0:
                chroma[12:24] /= np.sum(chroma[12:24] ** 2)
        elif chromaNorm == 'Linf':
            if np.sum(chroma[0:12]) != 0:
                chroma[0:12] /= np.max(np.abs(chroma[0:12]))
            if np.sum(chroma[12:24]) != 0:
                chroma[12:24] /= np.max(np.abs(chroma[12:24]))

        Xtarget.append(chroma)

    # batch train Neural Network
    trainNet(np.asarray(Xtrain), np.asarray(Xtarget), net, errorFunc, verbose)

    if verbose:
        print "Cleaning file pointers."

    qFile.close()
    cFile.close()

    return net

def trainNet(Xtrain, Xtarget, net, errorFunc, verbose = False):
    '''
    Train the neural net given the set of features.

    PARAMETERS
    ----------
    Xtrain {T,D1}: training data
    Xtarget {T,D2}: target data
    '''
    
    if verbose:
        print "Training ..."

    optArgs = {'wBounds': (-2,2), 'm': 10, 'factr': 1e7, 'pgtol': 1e-05, 'disp': verbose, 'maxfun': 15000}
    err = net.train(Xtrain, Xtarget, method='l_bfgs_b', error = errorFunc, **optArgs)

    if verbose:
        print "Done Training."

learnNNbuff(verbose = True, nnStruct = [256, 50, 24], errorFunc = 'KLDiv', chromaNorm = 'L1', constantQNorm = 'Linf')