
import numpy as np

# ┌──────────────────────────────┐
# │      MachineSimulator        │
# │ (optional, for visualizer)   │
# └──────────────────────────────┘

class MachineSimulator:
    def __init__(self, sim_params):
        self.sim_params = sim_params
    
    def get_sim_parameters(self):
        sim_params={}
        #to read from config later
        steppernames={'X','Y','Z','E'}
        posmin={'X':0,'Y':0,'Z':-5,'E':None}
        posmax={'X':234.00,'Y':235.00,'Z':245.00,'E':None}
        stepsperunit={'X':80.00,'Y':80.00,'Z':400.00,'E':93.00}
        feedratemax={'X':500,'Y':500,'Z':5,'E':25} #(units/s)
        accelerationmax={'X':500,'Y':500,'Z':100,'E':5000} #(units/s2)
        feedratedependancy={'X':1,'Y':1,'Z':1,'E':None} #if 1 will use the minfeedrate in case of a dependant axis movement
        sim_params.update({'steppernames':steppernames})
        sim_params.update({'posmin':posmin})
        sim_params.update({'posmax':posmax})
        sim_params.update({'stepsperunit':stepsperunit})
        sim_params.update({'feedratemax':feedratemax})
        sim_params.update({'feedratedependancy':feedratedependancy})
        sim_params.update({'accelerationmax':accelerationmax})        
        return sim_params
    
    def get_min_max_in_dict(self,adict,ismin=True):
        result=None
        for item in adict:
            val=adict[item]
            if ismin==True:                
                if val<=result or result is None:
                    result=val
            else:
                if val>=result or result is None:
                    result=val
        return result

    def get_sim_time(self,posini,posend,vini,vend):        
        evlist=[]
        allFR=self.sim_params['feedratemax']
        allAcc=self.sim_params['accelerationmax']
        FR={}
        Acc={}
        #only use the ones that have a different end position
        dep=self.sim_params('feedratedependancy')
        for xyze in self.sim_params('steppernames'):            
            try:
                if posini[xyze]!=posend[xyze] or vini[xyze]!=vend[xyze] and dep[xyze]==1:
                    evlist.append(xyze)
                    FR.update({xyze:allFR[xyze]})
                    Acc.update({xyze:allAcc[xyze]})
            except:
                pass
        #Find minimum Feedrate and acceleration on changing variables (will be used in moving)
        minFR=self.get_min_max_in_dict(FR,True)
        minAcc=self.get_min_max_in_dict(Acc,True)
        for xyze in posini:
            if dep[xyze]==1:
                FR.update({xyze:minFR})
                Acc.update({xyze:minAcc})
            else:
                FR.update({xyze:minFR})
                Acc.update({xyze:allAcc[xyze]})
        vel={}
        times={}
        for xyze in posini:
            ttt=self.get_cyn_time_block(posini[xyze],posend[xyze],vini[xyze],vend[xyze],Acc[xyze],FR[xyze])            
            times.update({xyze:ttt})
        return times
    
    def get_cyn_time_to_accelerate(self,Vi,Vf,Acc,Vmax):        
        if Vf>Vmax:
            Vf=Vmax        
        vvv=abs(Vf-Vi)
        if Acc==0 or Acc is None:
            return 0,Vf
        ttt= abs(vvv/Acc)
        return ttt,Vf
    
    def get_cyn_distance_to_accelerate(self,Vi,Vf,Acc,Vmax):        
        ttt,Vf=self.get_cyn_time_to_accelerate(Vi,Vf,Acc,Vmax)
        dX=Vi*ttt+0.5*Acc*ttt**2
        return abs(dX),ttt,Vf
    
    def get_cyn_time_block(self,Xi,Xf,Vi,Vf,Acc,Vmax):  
        dX=abs(Xf-Xi)
        if Vf>Vmax:
            Vf=Vmax                
        if Vi<Vf and Vf>0:            
            rqdX,rqttt,rqVf=self.get_cyn_distance_to_accelerate(Vi,Vf,Acc,Vmax)
            if dX>rqdX:
                ttt=rqttt+(dX-rqdX)/Vf
            else:
                ttt=self.get_cyn_time_position(self,0,dX,Vi,Acc)
        elif Vi>Vf and Vf>=0:
            rqdX,rqttt,rqVf=self.get_cyn_distance_to_accelerate(Vf,Vi,Acc,Vmax)
            if dX>rqdX:
                ttt=rqttt+(dX-rqdX)/Vf
            else:
                ttt=self.get_cyn_time_position(self,0,dX,Vi,Acc)
        elif Vi==Vf and Vf==0:
            rqdX,rqttt,rqVf=self.get_cyn_distance_to_accelerate(0,Vmax,Acc,Vmax)
            if dX>2*rqdX:
                ttt=2*rqttt+(dX-2*rqdX)/rqVf            
            else:
                ttt=2*self.get_cyn_time_position(self,0,dX/2,Vi,Acc)
        elif Vi==Vf and Vf!=0:            
            ttt=(dX)/Vf                        
        else:            
            ttt=0
        return ttt        

    def get_cyn_time_position(self,Xi,Xf,Vi,Acc):             
        dX=Xf-Xi
        aaa=1
        if Acc!=0:            
            bbb=Vi*2/Acc 
            ccc=-2*dX/Acc     
            insqr=bbb**2-4*aaa*ccc
        else:            
            insqr=-1        
        if insqr>=0:
            sol1=(-bbb+insqr**0.5)/(2*aaa)
            sol2=(-bbb-insqr**0.5)/(2*aaa)
            if sol1>=0 and sol2<0:
                ttt=sol1
            elif sol2>=0 and sol1<0: 
                ttt=sol2
            else:
                ttt=min(sol1,sol2)

        else:
            return 0
        
        return ttt
    
    #def get_sim_Position_at_dt(self,posini,posend,dt):
