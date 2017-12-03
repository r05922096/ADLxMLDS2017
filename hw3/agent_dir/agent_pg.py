from agent_dir.agent import Agent
import numpy as np
from agent_dir.RL import PolicyGradient

def prepro(I):
    """ prepro 210x160x3 uint8 frame into 5120 (80x64) 1D float vector """
    I = I[35:195] # crop
    I = I[:,16:-16]
    I = I[::2,::2,0] # downsample by factor of 2
    I[I == 144] = 0 # erase background (background type 1)
    I[I == 109] = 0 # erase background (background type 2)
    I[I != 0] = 1 # everything else (paddles, ball) just set to 1
    return I.astype(np.float).ravel()

class Agent_PG(Agent):
    def __init__(self, env, args):
        super(Agent_PG,self).__init__(env)

        # enviroment infomation
        print('Action Num:', env.action_space.n)
        print('Observe Shape:', env.observation_space.shape)

        # hyperparameters
        self.n_actions = 2
        self.n_features = 80 * 64
        self.n_hidden = 200 # number of hidden layer neurons
        
        # model
        self.model = PolicyGradient(
                        self.n_actions, 
                        self.n_features, 
                        n_hidden=self.n_hidden, 
                        learning_rate=0.0005, 
                        reward_decay=0.99, 
                        output_graph=False
                     )

        # load
        if args.test_pg:
            print('loading trained model')
            self.model.load('models/best_pg')


    def init_game_setting(self):
        """

        Testing function will call this function at the begining of new game
        Put anything you want to initialize if necessary

        """
        pass


    def train(self):
        try:
            for epoch in range(1,10000):
                pre_observation = None
                observation = self.env.reset()
                observation = prepro(observation)
                while True:
                    # diff_observation
                    feature_observation = observation if pre_observation is None else observation - pre_observation
                    pre_observation = observation

                    # transition
                    action = self.model.choose_action(feature_observation)
                    observation, reward, done, info = self.env.step(action+2)
                    observation = prepro(observation)

                    # store
                    self.model.store_transition(feature_observation, action, reward)

                    # slow motion
                    #print('\n', feature_observation.reshape((80,64))[:,-10:])
                    #print('\n', observation.reshape((80,64))[:,[0,1,2,3,-4,-3,-2,-1]])
                    #input()
                        
                    if done:
                        # show info
                        total_reward = sum(self.model.ep_rs)
                        print('episode:', epoch, '  reward:', int(total_reward))

                        # learn
                        self.model.learn()
                        break

        except KeyboardInterrupt:
            cmd = input('\nsave/load/keep/render/exit ?\n')
            if cmd == 'save' or cmd == 's':
                path = input('save path: ')
                self.model.save(path)
                self.train()
            if cmd == 'load' or cmd == 'l':
                path = input('load path: ')
                self.model.load(path)
                self.train()
            elif cmd == 'keep' or cmd == 'k':
                self.train()
            elif cmd == 'render' or cmd == 'r':
                self.env.do_render = not self.env.do_render
                self.train()
            elif cmd == 'exit' or cmd == 'e':
                pass
            return

        self.model.save('models/finish_pong_pg')
                

            

    def make_action(self, observation, test=True):
        """
        Return predicted action of your agent

        Input:
            observation: np.array
                current RGB screen of game, shape: (210, 160, 3)

        Return:
            action: int
                the predicted action from trained model
        """
        observation = prepro(observation)
        return self.model.choose_action(observation)
