# Code adapted from https://github.com/araffin/rl-baselines-zoo
# Author: Antonin Raffin

import os
import argparse

import gym
import numpy as np
from stable_baselines.common.vec_env import VecVideoRecorder, VecFrameStack, VecNormalize

from .utils import ALGOS, create_test_env, get_saved_hyperparams, ENV_ID, get_latest_run_id

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--folder', help='Log folder', type=str, default='logs')
parser.add_argument('-o', '--output-folder', help='Output folder', type=str, default='logs/videos/')
parser.add_argument('--algo', help='RL Algorithm', default='ppo2',
                    type=str, required=False, choices=list(ALGOS.keys()))
parser.add_argument('-n', '--n-timesteps', help='number of timesteps', default=1000,
                    type=int)
parser.add_argument('--deterministic', action='store_true', default=False,
                    help='Use deterministic actions')
parser.add_argument('--seed', help='Random generator seed', type=int, default=0)
parser.add_argument('--no-render', action='store_true', default=False,
                    help='Do not render the environment (useful for tests)')
parser.add_argument('-vae', '--vae-path', help='Path to saved VAE', type=str, default='')
parser.add_argument('--exp-id', help='Experiment ID (-1: no exp folder, 0: latest)', default=0,
                    type=int)
args = parser.parse_args()

algo = args.algo
folder = args.folder
video_folder = args.output_folder
seed = args.seed
deterministic = args.deterministic
video_length = args.n_timesteps

if args.exp_id == 0:
    args.exp_id = get_latest_run_id(os.path.join(folder, algo), ENV_ID)
    print('Loading latest experiment, id={}'.format(args.exp_id))

# Sanity checks
if args.exp_id > 0:
    log_path = os.path.join(folder, algo, '{}_{}'.format(ENV_ID, args.exp_id))
else:
    log_path = os.path.join(folder, algo)


model_path = "{}/{}.pkl".format(log_path, ENV_ID)

stats_path = os.path.join(log_path, ENV_ID)
hyperparams, stats_path = get_saved_hyperparams(stats_path)
hyperparams['vae_path'] = args.vae_path

env = create_test_env(stats_path=stats_path, seed=seed, log_dir=None,
                      hyperparams=hyperparams)

model = ALGOS[algo].load(model_path)

obs = env.reset()

# Note: apparently it renders by default
env = VecVideoRecorder(env, video_folder,
                       record_video_trigger=lambda x: x == 0, video_length=video_length,
                       name_prefix="{}-{}".format(algo, ENV_ID))

env.reset()
for _ in range(video_length + 1):
    # action = [env.action_space.sample()]
    action, _ = model.predict(obs, deterministic=deterministic)
    if isinstance(env.action_space, gym.spaces.Box):
        action = np.clip(action, env.action_space.low, env.action_space.high)
    obs, _, _, _ = env.step(action)

# Reset car
env.reset()
# Workaround for https://github.com/openai/gym/issues/893
env = env.venv
# DummyVecEnv
while isinstance(env, VecNormalize) or isinstance(env, VecFrameStack):
    env = env.venv
env.envs[0].env.close()
