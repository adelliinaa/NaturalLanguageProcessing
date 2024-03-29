import inspect, sys, hashlib

# Hack around a warning message deep inside scikit learn, loaded by nltk :-(
#  Modelled on https://stackoverflow.com/a/25067818
import warnings
with warnings.catch_warnings(record=True) as w:
    save_filters=warnings.filters
    warnings.resetwarnings()
    warnings.simplefilter('ignore')
    import nltk
    warnings.filters=save_filters
try:
    nltk
except NameError:
    # didn't load, produce the warning
    import nltk
import itertools
chain = itertools.chain.from_iterable

from nltk.corpus import brown
from nltk.tag import map_tag, tagset_mapping
# module for training a Hidden Markov Model and tagging sequences
from nltk.tag.hmm import HiddenMarkovModelTagger
# module for computing a Conditional Frequency Distribution
from nltk.probability import ConditionalFreqDist
# module for computing a Conditional Probability Distribution
from nltk.probability import ConditionalProbDist, LidstoneProbDist

if map_tag('brown', 'universal', 'NR-TL') != 'NOUN':
    # Out-of-date tagset, we add a few that we need
    tm=tagset_mapping('en-brown','universal')
    tm['NR-TL']=tm['NR-TL-HL']='NOUN'

class HMM:
    def __init__(self, train_data, test_data):
        """
        Initialise a new instance of the HMM.
        :param train_data: The training dataset, a list of sentences with tags
        :type train_data: list(list(tuple(str,str)))
        :param test_data: the test/evaluation dataset, a list of sentence with tags
        :type test_data: list(list(tuple(str,str)))
        """
        self.train_data = train_data
        self.test_data = test_data

        # Emission and transition probability distributions
        self.emission_PD = None
        self.transition_PD = None
        self.states = []

        self.viterbi = []
        self.backpointer = []

    # Compute emission model using ConditionalProbDist with a LidstoneProbDist estimator.
    #   To achieve the latter, pass a function
    #    as the probdist_factory argument to ConditionalProbDist.
    #   This function should take 3 arguments
    #    and return a LidstoneProbDist initialised with +0.01 as gamma and an extra bin.
    #   See the documentation/help for ConditionalProbDist to see what arguments the
    #    probdist_factory function is called with.
    def emission_model(self, train_data):
        """
        Compute an emission model using a ConditionalProbDist.
        :param train_data: The training dataset, a list of sentences with tags
        :type train_data: list(list(tuple(str,str)))
        :return: The emission probability distribution and a list of the states
        :rtype: Tuple[ConditionalProbDist, list(str)]
        """
        #raise NotImplementedError('HMM.emission_model')
        # TODO prepare data

        # Don't forget to lowercase the observation otherwise it mismatches the test data
        # Do NOT add <s> or </s> to the input sentences
        # Each data item is under the form (tag - condition, word - observation)
        
        #print(train_data)
        data = []
        for i in train_data:
          for (word,tag) in i:
            data.append((tag,word.lower()))

        emission_FD = ConditionalFreqDist(data)
        self.emission_PD = ConditionalProbDist(emission_FD, lambda f:nltk.probability.LidstoneProbDist(f,0.01,f.B()+1))
        self.states = list(set([tag for (tag,word) in data]))

        return self.emission_PD, self.states


    # Access function for testing the emission model
    # For example model.elprob('VERB','is') might be -1.4
    def elprob(self,state,word):
        """
        The log of the estimated probability of emitting a word from a state
        :param state: the state name
        :type state: str
        :param word: the word
        :type word: str
        :return: log base 2 of the estimated emission probability
        :rtype: float
        """
        # raise NotImplementedError('HMM.elprob')
        return self.emission_PD[state].logprob(word)

    # Compute transition model using ConditionalProbDist with a LidstonelprobDist estimator.
    # See comments for emission_model above for details on the estimator.
    def transition_model(self, train_data):
        """
        Compute an transition model using a ConditionalProbDist.
        :param train_data: The training dataset, a list of sentences with tags
        :type train_data: list(list(tuple(str,str)))
        :return: The transition probability distribution
        :rtype: ConditionalProbDist
        """
        # raise NotImplementedError('HMM.transition_model')
        data = []
        for s in train_data:
          # Start of sentance
          last = '<s>' 
          for (word, transition) in s:
            data.append((last, transition))
            last = transition
          # End of sentence
          data.append((last, '</s>')) 

        transition_FD = ConditionalFreqDist(data)
        self.transition_PD = ConditionalProbDist(transition_FD, lambda f:nltk.probability.LidstoneProbDist(f,0.01,f.B()+1))

        return self.transition_PD

    # Access function for testing the transition model
    # For example model.tlprob('VERB','VERB') might be -2.4
    def tlprob(self,state1,state2):
        """
        The log of the estimated probability of a transition from one state to another
        :param state1: the first state name
        :type state1: str
        :param state2: the second state name
        :type state2: str
        :return: log base 2 of the estimated transition probability
        :rtype: float
        """
        # raise NotImplementedError('HMM.tlprob')
        return self.transition_PD[state1].logprob(state2)

    # Train the HMM
    def train(self):
        """
        Trains the HMM from the training data
        """
        self.emission_model(self.train_data)
        self.transition_model(self.train_data)

    # Part B: Implementing the Viterbi algorithm.

    # Initialise data structures for tagging a new sentence.
    # Describe the data structures with comments.
    # Use the models stored in the variables: self.emission_PD and self.transition_PD
    # Input: first word in the sentence to tag
    def initialise(self, observation):
        """
        Initialise data structures for tagging a new sentence.
        :param observation: the first word in the sentence to tag
        :type observation: str
        """
        # raise NotImplementedError('HMM.initialise')
        # Initialise step 0 of viterbi, including
        #  transition from <s> to observation
        # use costs (-log-base-2 probabilities)
        # if the backpointer is 0 means this word is at the beginning
        
                
        # Initialise viterbi and backpointer
        self.viterbi.clear()
        self.backpointer.clear()
        # logprob of sentence starting with a state + logprob of the first word | state
        # logprob of sent starting with the state | word
        # => addition of costs: log P(tag | <s>) + log P(word | tag)
        self.viterbi.append([-(self.transition_PD['<s>'].logprob(state) + self.emission_PD[state].logprob(observation)) for state in self.states])
        self.backpointer.append([-1 for i in self.states])

    # Tag a new sentence using the trained model and already initialised data structures.
    # Use the models stored in the variables: self.emission_PD and self.transition_PD.
    # Update the self.viterbi and self.backpointer datastructures.
    # Describe your implementation with comments.
    def tag(self, observations):
        """
        Tag a new sentence using the trained model and already initialised data structures.
        :param observations: List of words (a sentence) to be tagged
        :type observations: list(str)
        :return: List of tags corresponding to each word of the input
        """
        # raise NotImplementedError('HMM.tag')

        # reference: https://web.stanford.edu/~jurafsky/slp3/A.pdf
        
        tags = []
        cMin = [float('inf')]
        step = 0
        i = 0
        for t in [word.lower() for word in observations]: 
            # Viterbi and backpointer columns
            viterbi = cMin * len(self.states)             
            backpointer = [-1] * len(self.states)       
            # Compute and find the lowest cost
            for step0 in self.states:   
                for step1 in self.states:  # for each current possible state, find the best last state
                    # Sum up the transition, emission and the cost of the previous step
                    cost = -(self.transition_PD[step1].logprob(step0) + self.emission_PD[step0].logprob(t)) + self.get_viterbi_value(step1, step)
                    # Check whether there is a lower cost
                    if cost < viterbi[self.states.index(step0)]:
                        viterbi[self.states.index(step0)] = cost
                        backpointer[self.states.index(step0)] = self.states.index(step1)
            step += 1  
            # Update viterbi and backpointer 
            self.viterbi.append(viterbi)
            self.backpointer.append(backpointer)

        # Cost of transition to </s> 
        terminate = [0] * len(self.states)  
        for step0 in self.states:
            terminate[i] = self.get_viterbi_value(step0, step) - self.tlprob(step0, '</s>')
            i += 1
        # Get minimum cost
        backpointer = self.states[terminate.index(min(terminate))]

        while backpointer != '<s>':
            tags.append(backpointer)
            backpointer = self.get_backpointer_value(backpointer, step)
            step -= 1
        
        tags.reverse()

        return tags


    def get_viterbi_value(self, state, step):
        """
        Return the current value from self.viterbi for
        the state (tag) at a given step
        :param state: A tag name
        :type state: str
        :param step: The (0-origin) number of a step:  if negative,
          counting backwards from the end, i.e. -1 means the last step
        :type step: int
        :return: The value (a cost) for state as of step
        :rtype: float
        """
        # raise NotImplementedError('HMM.get_viterbi_value')
        return self.viterbi[step][self.states.index(state)]


    def get_backpointer_value(self, state, step):
        """
        Return the current backpointer from self.backpointer for
        the state (tag) at a given step
        :param state: A tag name
        :type state: str
        :param step: The (0-origin) number of a step:  if negative,
          counting backwards from the end, i.e. -1 means the last step
        :type step: int
        :return: The state name to go back to at step-1
        :rtype: str
        """
        # raise NotImplementedError('HMM.get_backpointer_value')

        if step == 0 or step == -len(self.viterbi):
            return '<s>'
        elif state == '</s>' and (step == len(self.viterbi) - 1 or step == -1):
            return self.states[self.backpointer[step][0]]
        else:
            return self.states[self.backpointer[step][self.states.index(state)]]

def answer_question4b():
    """
    Report a hand-chosen tagged sequence that is incorrect, correct it
    and discuss
    :rtype: list(tuple(str,str)), list(tuple(str,str)), str
    :return: your answer [max 280 chars]
    """
    # raise NotImplementedError('answer_question4b')

    tagged_sequence = [('Tooling', 'ADV'), ('through', 'ADP'), ('Sydney', 'NOUN'), ('on', 'ADP'), ('his', 'DET'), ('way', 'NOUN'), ('to', 'ADP'), ('race', 'NOUN'), ('in', 'ADP'), ('the', 'DET'), ('New', 'ADJ'), ('Zealand', 'X'), ('Grand', 'X'), ('Prix', 'X')]
    correct_sequence = [('Tooling', 'ADV'), ('through', 'ADP'), ('Sydney', 'NOUN'), ('on', 'ADP'), ('his', 'DET'), ('way', 'NOUN'), ('to', 'ADP'), ('race', 'NOUN'), ('in', 'ADP'), ('the', 'DET'), ('New', 'NOUN'), ('Zealand', 'NOUN'), ('Grand', 'X'), ('Prix', 'X')]

    answer =  inspect.cleandoc("""In our model, the probaility of'New' being used as an adjective after the article 'the' is higher than the probability oF being used as a personal noun. As the algorithm does not capture longer word sequences, some potentially useful distinctions are lost, such as named-entity recognition, and it can tag ambiguous words with their most frequent label. Entity recognition (location in the given example) is the core of the information extraction systems. Ambiguity between named entities and common words ('New' as an adjective or personal noun) is an issue here.""")[0:280]
    
    return tagged_sequence, correct_sequence, answer

def answer_question5():
    """
    Suppose you have a hand-crafted grammar that has 100% coverage on
        constructions but less than 100% lexical coverage.
        How could you use a POS tagger to ensure that the grammar
        produces a parse for any well-formed sentence,
        even when it doesn't recognise the words within that sentence?
    :rtype: str
    :return: your answer [max 500 chars]
    """
    # raise NotImplementedError('answer_question5')
    return inspect.cleandoc("""To ensure that the grammar produces a parse for any well-formed sentence, we consider 2 cases: For unseen words and ambiguities, we use the pre-trained POS tagger to find the most likely tag bases on the transition probability. For any other word, we use the output generated by the original parser (using a tree of the sentence based on the POS instead of the actual words).""")[0:500]


def answer_question6():
    """
    Why else, besides the speedup already mentioned above, do you think we
    converted the original Brown Corpus tagset to the Universal tagset?
    What do you predict would happen if we hadn't done that?  Why?
    :rtype: str
    :return: your answer [max 500 chars]
    """
    # raise NotImplementedError('answer_question6')
    return inspect.cleandoc("""The Universal tag set comprises of 12 tag classes, whereas the Brown Corpus consists of 87. We use the first one in order to get more precise estimates for both the emission and transition probabilities. Using the latter would result in less accurate probabilities, as the possibility of each word taking 87 tags would result in many emission and transition probabilities close to 0 and hence, many errors in the POS tag.""")[0:500]

# Useful for testing
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    # http://stackoverflow.com/a/33024979
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def answers():
    global tagged_sentences_universal, test_data_universal, \
           train_data_universal, model, test_size, train_size, ttags, \
           correct, incorrect, accuracy, \
           good_tags, bad_tags, answer4b, answer5

    # Load the Brown corpus with the Universal tag set.
    tagged_sentences_universal = brown.tagged_sents(categories='news', tagset='universal')

    # Divide corpus into train and test data.
    test_size = 500
    train_size = len(tagged_sentences_universal) - test_size

    test_data_universal = tagged_sentences_universal[-test_size:] # fixme
    train_data_universal = tagged_sentences_universal[:train_size] # fixme

    if hashlib.md5(''.join(map(lambda x:x[0],train_data_universal[0]+train_data_universal[-1]+test_data_universal[0]+test_data_universal[-1])).encode('utf-8')).hexdigest()!='164179b8e679e96b2d7ff7d360b75735':
        print('!!!test/train split (%s/%s) incorrect, most of your answers will be wrong hereafter!!!'%(len(train_data_universal),len(test_data_universal)),file=sys.stderr)

    # Create instance of HMM class and initialise the training and test sets.
    model = HMM(train_data_universal, test_data_universal)

    # Train the HMM.
    model.train()

    # Some preliminary sanity checks
    # Use these as a model for other checks
    e_sample=model.elprob('VERB','is')
    if not (type(e_sample)==float and e_sample<=0.0):
        print('elprob value (%s) must be a log probability'%e_sample,file=sys.stderr)

    t_sample=model.tlprob('VERB','VERB')
    if not (type(t_sample)==float and t_sample<=0.0):
           print('tlprob value (%s) must be a log probability'%t_sample,file=sys.stderr)

    if not (type(model.states)==list and \
            len(model.states)>0 and \
            type(model.states[0])==str):
        print('model.states value (%s) must be a non-empty list of strings'%model.states,file=sys.stderr)

    print('states: %s\n'%model.states)

    ######
    # Try the model, and test its accuracy [won't do anything useful
    #  until you've filled in the tag method
    ######
    s='the cat in the hat came back'.split()
    model.initialise(s[0])
    ttags = model.tag(s[1:])
    print("Tagged a trial sentence:\n  %s"%list(zip(s,ttags)))

    v_sample=model.get_viterbi_value('VERB',5)
    if not (type(v_sample)==float and 0.0<=v_sample):
           print('viterbi value (%s) must be a cost'%v_sample,file=sys.stderr)

    b_sample=model.get_backpointer_value('VERB',5)
    if not (type(b_sample)==str and b_sample in model.states):
           print('backpointer value (%s) must be a state name'%b_sample,file=sys.stderr)

    # check the model's accuracy (% correct) using the test set
    correct = 0
    incorrect = 0

    idx = 0
    POS = []
    sent = []
    for sentence in test_data_universal:
        wrong = False
        s = [word.lower() for (word, tag) in sentence]
        model.initialise(s[0])
        tags = model.tag(s[1:])

        for ((word,gold),tag) in zip(sentence,tags):
            if tag == gold:
                correct+=1
            else:
                incorrect+=1
                wrong = True
        if wrong and idx < 10:
            idx+=1
            sent.append(sentence)
            orig = [word for (word, tag) in sentence]
            POS.append(list(zip(orig, tags)))
    print(sent)
    print(POS)

    # Calculate the accuracy
    accuracy = correct/(correct+incorrect)
    print('Tagging accuracy for test set of %s sentences: %.4f'%(test_size,accuracy))

    # Print answers for 4b, 5 and 6
    bad_tags, good_tags, answer4b = answer_question4b()
    print('\nA tagged-by-your-model version of a sentence:')
    print(bad_tags)
    print('The tagged version of this sentence from the corpus:')
    print(good_tags)
    print('\nDiscussion of the difference:')
    print(answer4b[:280])
    answer5=answer_question5()
    print('\nFor Q5:')
    print(answer5[:500])
    answer6=answer_question6()
    print('\nFor Q6:')
    print(answer6[:500])


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1] == '--answers':
        import adrive2_embed
        from autodrive_embed import run, carefulBind
        with open("userErrs.txt","w") as errlog:
            run(globals(),answers,adrive2_embed.a2answers,errlog)
    else:
        answers()
