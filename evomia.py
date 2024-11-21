import numpy as np
import os
import sys
import subprocess as sp
import time
import json
from utils import InpWriter, JsonReader
import optuna
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TimeElapsedColumn

class ThresholdExceeded(optuna.exceptions.OptunaError):
    pass
class EVOMIA:
    def __init__(self,
                 obj_name:str='neck',
                 material:str='linear',
                 output:str='integrated_force',
                 max_trials:int=100,
                 max_time:int=3600,
                 err_threshold:float=1e-3,
                 batch_size:int=8) -> None:
        '''
        Parameter Optimization class
        This class is designed to perform optimization of model parameters in Abaqus.

        Args:
            obj_name: str, object name
            material: str, material name
            output: str, output name
            max_trials: int, maximum iteration
            max_time: int, maximum time
            err_threshold: float, error threshold
            batch_size: int, batch size

        Returns:
            None

        Raises:
            ValueError: if the opt_gt is empty
            FileNotFoundError: if the inp_template is not found
        '''
        # Parameter Optimization
        print('\033[7m{:=^70s}\033[0m'.format(' EVOMIA '))

        # Initialization
        print('{:-^70s}'.format(' INITIALIZATION '))
        if obj_name == 'example':
            self.opt_name = 'example'
        else:
            self.opt_name = obj_name + '_' + material + '_' + output + time.strftime('_%Y%m%d-%H%M%S')
        self.opt_params = json.load(open('templates/material/' + material + '.json', 'r'))
        print('Optimization parameters:', [key for key in self.opt_params.keys()])
        self.output = output
        self.opt_gt = list(json.load(open('data/ground_truth/' + obj_name + '_' + material + '_' + output + '.json', 'r')).values())
        print('Optimization targets:', [key for key in self.opt_gt[0]["output"].keys()])
        self.inp_template = 'templates/inp/' + obj_name + '_' + material + '.inp'
        print('Input file template:', self.inp_template)
        self.max_trials = max_trials
        print('Maximum iteration:', self.max_trials)
        self.max_time = max_time
        print('Maximum time:', self.max_time)
        self.err_threshold = err_threshold
        print('Error threshold:', self.err_threshold)
        self.opt_path = 'data/' + self.opt_name + '/'
        print('Optimization path:', self.opt_path)
        self.inp_writer = InpWriter(inp_template=self.inp_template)
        self.json_reader = JsonReader()
        self.batch_size = batch_size
        self.counter = 0
        
        # Check if the input parameters are valid
        try:
            if self.opt_gt == {}:
                raise ValueError('\033[31mERROR: GROUND TRUTH IS EMPTY !!!\033[0m')
            if not os.path.exists(self.inp_template):
                raise FileNotFoundError('\033[31mERROR: INP TEMPLATE NOT FOUND !!!\033[0m')
        except (ValueError, FileNotFoundError) as e:
            print(e)
            sys.exit()
        
        # Create optimization path
        if not os.path.exists(self.opt_path):
            os.makedirs(self.opt_path)

        # Save configuration
        with open(self.opt_path + 'config.json', 'w') as f:
            json.dump({'Optimization parameters': self.opt_params,
                       'Optimization targets': self.opt_gt,
                       'Input file template': self.inp_template,
                       'Maximum iteration': self.max_trials,
                       'Maximum time': self.max_time,
                       'Error threshold': self.err_threshold,
                       'Batch size': self.batch_size},
                      f,
                      sort_keys=True,
                      indent=4,
                      separators=(',', ': '))
    
    def cal_error(self,
                  res:dict,
                  gt:dict) -> dict:
        '''
        Check error

        Args:
            res: dict, optimization results
            gt: dict, optimization ground truth

        Returns:
            err: dict, error
        '''

        err = {key: 0 for key in gt.keys()}
        for key in gt.keys():
            err[key] = float(res[key]) - float(gt[key])
        
        return err
    
    def objective(self,
                  trial:optuna.Trial) -> float:
        '''
        Objective function

        Args:
            trial: optuna.Trial, optimization trial

        Returns:
            err_mean: float, mean error
        '''

        self.counter += 1
        # print('{:-^70s}'.format(' TRIAL ' + str(self.counter) + ' '))

        param_vals = dict()
        for key in self.opt_params.keys():
            param_vals[key] = trial.suggest_float(key, 
                                                  self.opt_params[key][0], 
                                                  self.opt_params[key][1])

        # Init result list
        results = list()

        # Write input file
        with Progress("[progress.description]{task.description}", 
                      BarColumn(), 
                      "[progress.percentage]{task.percentage:>3.0f}%", 
                      TimeRemainingColumn(), 
                      TimeElapsedColumn()) as progress:
            writing_task = progress.add_task("Writing", 
                                             total=len(self.opt_gt))
            
            for num in range(len(self.opt_gt)):
                inp = self.opt_path + str(self.counter) + '_' + str(num) + '.inp'
                self.inp_writer.write(inp, 
                                      {**param_vals,
                                       **self.opt_gt[num]["input"]})
                progress.update(writing_task, 
                                advance=1)
            
            progress.refresh()
        
        # Run Abaqus
        with Progress("[progress.description]{task.description}", 
                      BarColumn(), 
                      "[progress.percentage]{task.percentage:>3.0f}%", 
                      TimeRemainingColumn(), 
                      TimeElapsedColumn()) as progress:
            running_task = progress.add_task("Running", 
                                             total=len(self.opt_gt))

            for batch in range(0, len(self.opt_gt), self.batch_size):
                processes = list()
                for num in range(batch, min(batch + self.batch_size, len(self.opt_gt))):
                    process = sp.Popen('abaqus job=' + str(self.counter) + '_' + str(num) + ' cpus=4 int', 
                                    cwd=self.opt_path,
                                    shell=True, 
                                    stdout=sp.DEVNULL, 
                                    stderr=sp.STDOUT)
                    processes.append(process)

                finished_count = 0
                while True:
                    for process in processes:
                        process.communicate()
                        if process.poll() is not None:
                            finished_count += 1
                            progress.update(running_task, advance=1)
                    if finished_count == len(self.opt_gt):
                        break

                progress.refresh()

        # Read results
        with Progress("[progress.description]{task.description}", 
                      BarColumn(), 
                      "[progress.percentage]{task.percentage:>3.0f}%", 
                      TimeRemainingColumn(), 
                      TimeElapsedColumn()) as progress:
            reading_task = progress.add_task("Reading", 
                                             total=len(self.opt_gt))

            odbs = [str(self.counter) + '_' + str(num) + '.odb' for num in range(len(self.opt_gt))]
            for batch in range(0, len(self.opt_gt), self.batch_size):
                processes = list()
                for num in range(batch, min(batch + self.batch_size, len(self.opt_gt))):
                    process = sp.Popen('abaqus cae noGUI=odb_exporter.py -- ' + str(self.opt_path) + ' ' + str(odbs[num]) + ' ' + str(self.output),
                                       cwd='utils',
                                       shell=True,
                                       stdout=sp.DEVNULL,
                                       stderr=sp.STDOUT)
                    processes.append(process)

                finished_count = 0
                while True:
                    for num, process in enumerate(processes):
                        process.communicate()
                        if process.poll() is not None:
                            finished_count += 1
                            results.append(self.json_reader.read(path=self.opt_path,
                                                                 odb=odbs[batch + num]))
                            progress.update(reading_task, 
                                            advance=1)
                    if finished_count == len(self.opt_gt):
                        break

                progress.update(reading_task, advance=1)

            progress.refresh()

            # Remove abaqus.rpy files
            for file in os.listdir('utils'):
                if file.startswith('abaqus.rpy'):
                    os.remove('utils/' + file)

        # Calculate error
        errs = list()
        for i, result in enumerate(results):
            if result == {}:
                return float('nan')
            err = self.cal_error(result, 
                                 self.opt_gt[i]["output"])
            err_norm = np.linalg.norm([err[key] for key in err.keys()])
            errs.append(err_norm)
        err_mean = np.mean(errs, axis=0)

        print('Error:', err_mean)
        print('Parameters:', param_vals)

        return err_mean
    
    def check_threshold(self, 
                        study, 
                        trial):
        if study.best_value < self.err_threshold:
            raise ThresholdExceeded()

    def run(self) -> None:
        '''
        Run optimization
        This function is designed to run optimization.
        Optuna is used as the optimization library.
        CMAES is used as the sampler.
        '''

        print('{:-^70s}'.format(' OPTIMIZATION STARTED '))
        # Create study
        study = optuna.create_study(storage='sqlite:///databoard.sqlite3',
                                    study_name=self.opt_name,
                                    sampler=optuna.samplers.CmaEsSampler())
        
        # Set user attributes
        study.set_user_attr('Optimization parameters', 
                            [key for key in self.opt_params.keys()])
        study.set_user_attr('Optimization targets', 
                            self.opt_gt)
        study.set_user_attr('Maximum trial', 
                            self.max_trials)
        study.set_user_attr('Maximum time', 
                            self.max_time)
        study.set_user_attr('Error threshold', 
                            self.err_threshold)

        # Start optimization
        try:
            study.optimize(self.objective, 
                        n_trials=self.max_trials,
                        timeout=self.max_time,
                        callbacks=[self.check_threshold])
            print('{:-^70s}'.format(' OPTIMIZATION FINISHED '))
            print('Error:', study.best_value)
            print('Best parameters:', study.best_params)
        except ThresholdExceeded:
            print('{:-^70s}'.format(' THRESHOLD EXCEEDED '))
            print('{:-^70s}'.format(' OPTIMIZATION FINISHED '))
            print('Error:', study.best_value)
            print('Best parameters:', study.best_params)

if __name__ == '__main__':
    # Parameters
    obj_name = 'cylinder'
    material = 'linear'
    output = 'integrated_force'
    max_trials = 500
    max_time = 36000
    err_threshold = 1e-3
    batch_size = 8

    # Initialize auto optimization
    opt = EVOMIA(obj_name=obj_name,
                 material=material,
                 output=output,
                 max_trials=max_trials,
                 max_time=max_time,
                 err_threshold=err_threshold,
                 batch_size=batch_size)
    
    # Run optimization
    opt.run()