"""Small host-prepared timed worlds. No physical vehicle or environment setup."""
from dataclasses import dataclass
from .records import digest

@dataclass(frozen=True)
class LaneWorld:
    environment_id:str
    ready:bool
    lane:int=1
    step:int=0
    alive:bool=True
    def observe(self,obstacle):
        if not self.ready:raise ValueError('Harness or human must prepare and verify the environment')
        if type(obstacle) is not int or obstacle not in (0,1,2):raise ValueError('Invalid obstacle')
        return dict(environment_id=self.environment_id,step=self.step,lane=self.lane,obstacle=obstacle,deadline_ms=100)
    def act(self,observation,action,elapsed_ms):
        if not self.alive:raise ValueError('Episode ended')
        if observation!=self.observe(observation['obstacle']):raise ValueError('Stale or foreign observation')
        if action not in ('left','stay','right') or type(elapsed_ms) not in (int,float) or not 0<=elapsed_ms<float('inf'):raise ValueError('Invalid action timing')
        lane=min(2,max(0,self.lane+{'left':-1,'stay':0,'right':1}[action]))
        on_time=elapsed_ms<=observation['deadline_ms'];safe=lane!=observation['obstacle'];alive=on_time and safe
        next_state=LaneWorld(self.environment_id,True,lane,self.step+1,alive)
        return next_state,dict(on_time=on_time,collision_free=safe,passed=alive,timing_source='caller-supplied measurement; simulated timing in reference fixtures')
