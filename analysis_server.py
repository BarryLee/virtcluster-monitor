
import pdb
import logging
import logging.config

from SimpleXMLRPCServer import SimpleXMLRPCServer
from time import sleep
import select
import fcntl
import os
import threading

from monserver.utils.utils import threadinglize
from mon_analyst_cont import Analyst, AnalystState, AnalystException

logging.config.fileConfig(os.path.dirname(os.path.abspath(__file__)) + '/' + 'logging.conf.anas')

logger = logging.getLogger('analysis.analysis_server.py')

BLKSZ = 4096
BUFSZ = 1*1024**2

class AnalystManagerException(Exception):
    def __init__(self, msg):
        self.msg = msg

class AnalystManager(threading.Thread):

    _lock = threading.RLock()

    def __init__(self, log_dir, analysis_log_dir):
        self.log_dir = log_dir
        self.fp2analysts = {}
        self.appid2analysts = {}
        self.open_files = []
        self.RUNNING = False
        super(AnalystManager, self).__init__()
        self.daemon = True
        self.analysis_log_dir = analysis_log_dir

    def get_analysis_log_path(self, appid):
        return self.analysis_log_dir + '/' + appid + '.html'

    def get_analysis_progress(self, appid):
        r = {'state':''}
        if not self.appid2analysts.has_key(appid):
            r['state'] = AnalystState.stopped
        else:
            analyst = self.appid2analysts[appid]
            r['state'] = state = analyst.get_state()
            if state == AnalystState.preparing:
                r['num_obs'] = analyst.num_obs
                r['num_metrics'] = analyst.num_metrics
            elif state == AnalystState.running:
                r['im_results'] = analyst.im_results
                r['num_metrics'] = analyst.num_metrics
            elif state == AnalystState.maintain or state == AnalystState.evaluating:
                r['im_results'] = analyst.im_results
                r['fn_result'] = analyst.fn_result
                r['num_metrics'] = analyst.num_metrics
            elif state == AnalystState.error:
                raise AnalystManagerException, 'analyst error'

        return r

    def enable_analysis(self, appid, config={}):
        if self.appid2analysts.has_key(appid):
            return "OK"
        logger.info('Enabling analysis for app %s' % appid)
        analyst = Analyst(appid, config)
        #analyst.running = False
        analyst.set_state('preparing')
        ana_log = self.get_analysis_log_path(appid)
        logger.debug(ana_log)
        analyst.analysis_log = open(ana_log, 'w+')
        logger.debug(analyst.analysis_log)

        target_id = analyst.target
        logfile = self.log_dir + '/' + '_'.join([target_id, 'access_log'])
        self.register(logfile, analyst)
        self.appid2analysts[appid] = analyst

        info = { 'num_metrics': analyst.num_metrics }
        return info

    def disable_analysis(self, appid):
        try:
            analyst = self.get_analyst(appid)
        except AnalystManagerException, e:
            logger.exception('')
            return
        logger.info('disabling analysis for app %s' % appid)
        analyst.set_state(AnalystState.stopped)
        try:
            self.unregister(self.appid2analysts[appid])
        except IOError, e:
            logger.exception('')
        del self.appid2analysts[appid]
        logger.debug(self.appid2analysts)
        
    def register(self, logfile, analyst):
        fp = open(logfile)
        #fd = fp.fileno()
        #logger.debug(os.read(fd, 1024))
        logger.info('registering file descriptor for log file %s' % logfile)
        self.open_files.append(fp)
        self.fp2analysts[fp] = analyst

    def unregister(self, analyst):
        logger.debug('unregistering file descriptor')
        the_fp = None
        for fp, this_analyst in self.fp2analysts.items():
            if this_analyst is analyst:
                the_fp = fp
                break
        if the_fp is None:
            raise AnalystManagerException, 'fp2analysts corrupted!'
        del self.fp2analysts[the_fp]
        try:
            the_fp.close()
        except IOError, e:
            logger.exception('')
        finally:
            the_fp.close()

    def get_analyst(self, appid):
        try:
            return self.appid2analysts[appid]
        except KeyError, e:
            raise AnalystManagerException, \
                    'analysis for app %s is not enabled' % appid

    def log_update_loop(self):
        while self.RUNNING:
            shall_sleep = True
            #logger.debug('1st loop')
            #logger.debug(self.fd2analysts)
            for fp, analyst in self.fp2analysts.items():
                #logger.debug('2nd loop')
                new_data = []
                new_data_sz = 0
                while new_data_sz < BUFSZ:
                    try:
                    #logger.debug('3rd loop')
                    #chunk = os.read(fd, BUFSZ)
                        chunk = fp.readline()
                        if not chunk:
                            break
                        new_data_sz += len(chunk)
                        new_data.append(chunk)
                    except IOError, e:
                        logger.exception('')
                        break
                # end while
                #logger.debug(new_data_sz)
                if len(new_data):
                    shall_sleep = False
                    #logger.debug('break from 3rd loop')
                    #print new_data
                    self.update_analyst(analyst, new_data)
            # end for
            if shall_sleep: sleep(1)
        # end while

    def run(self):
        logger.info('starting main loop')
        self.RUNNING = True
        self.log_update_loop()

    def stop(self):
        logger.info('stoping main loop')
        self.RUNNING = False
        self.cleanup()

    def cleanup(self):
        for fp in self.open_files:
            fp.close()

    def update_analyst(self, analyst, data):
        analyst.update(data)

    def start_analysis(self, appid):
        try:
            analyst = self.appid2analysts[appid]
        except KeyError, e:
            raise AnalystManagerException, \
                    'analysis for app %s is not enabled' % appid
        cont = False
        self._lock.acquire()
        #if not analyst.running:
        if analyst.get_state() == AnalystState.preparing:
            #analyst.running = True
            if not analyst.ready4analysis():
                self._lock.release()
                raise AnalystManagerException, \
                        'app %s: no enough data for learning' % appid
            analyst.set_state('running')
            cont = True
        self._lock.release()
        if not cont:
            raise AnalystManagerException, \
                    'analysis for app %s is already started' % appid
        else:
            threadinglize(self._start_analysis)(analyst)

    def _start_analysis(self, analyst):
        #analyst = self.appid2analysts[appid]
        #if analyst.ready4analysis():
        try:
            analyst.im_results = []
            analyst.im_result_details = []
            #analyst.fn_result = [analyst.im_results]
            analyst.fn_result = []
            for res in analyst.do_analysis():
                #print res
                if res[-1]:
                    metric, score = analyst.metrics[res[0]], res[1]
                    metric[1]['threshold'] = analyst.get_feature_val(res[0])
                    analyst.im_results.append([metric, score])
                    # (*o*)
                    analyst.im_result_details.append(res[2:-1])
                # (*o*)
                self.log_im_result(analyst, res)
                if analyst.get_state() != AnalystState.running:
                    break
            if analyst.get_state() != AnalystState.stopped:
                #analyst.fn_result.append([
                #        [analyst.metrics[i] for i in analyst.learner.attrs_selected],
                #        analyst.learner.max_score])
                analyst.fn_result = [
                        [analyst.metrics[i] for i in sorted(analyst.learner.attrs_selected)],
                        analyst.learner.max_score]
                analyst.finish_analysis()
        except Exception, e:
            logger.exception('')
            analyst.set_state(AnalystState.error)
        finally:
            self._lock.acquire()
            #analyst.running = False
            analyst.set_state(AnalystState.maintain)
            self._lock.release()
            analyst.analysis_log.close()
      
    def stop_analysis(self, appid):
        analyst = self.get_analyst(appid)
        self._lock.acquire()
        if analyst.get_state() != AnalystState.running:
            self._lock.release()
            raise AnalystManagerException, 'analysis is not running'
        analyst.set_state(AnalystState.finishing)
        analyst.stop_analysis()
        self._lock.release()

    def start_evaluation(self, appid):          
        analyst = self.get_analyst(appid)
        analyst.start_post_evaluation()

    def get_evaluation_results(self, appid, start_from=0, qsize=0):
        analyst = self.get_analyst(appid)
        if not hasattr(analyst, 'evaluation_results'):
            raise AnalystManagerException, 'evaluation is not running'
        evaluation_results = analyst.evaluation_results
        results = evaluation_results['results']
        tc = evaluation_results['tc']
        end_b4 = min(qsize+start_from, tc) if qsize else tc
        #pdb.set_trace()
        ret = {'tc': tc,
               'fc': evaluation_results['fc'],
               'results': results[start_from:end_b4],
               'next': end_b4}
        return ret

    def stop_evaluation(self, appid):
        analyst = self.get_analyst(appid)
        analyst.stop_post_evaluation()

    def log_im_result(self, analyst, result):
        if result[-1] == 0:
            splitline = '=' * 50
            ssplitline = '-' * 46
            metrics = ''
            for n,i in enumerate(result[1][:-1]):
                if n % 3 == 2:
                    metrics += '\n'
                metrics += '%s(%s) ' % (analyst.metrics[i][1]['name'],
                                        analyst.metrics[i][0])
            logger.debug(metrics)
            html = """\
<br><pre>
model #%d
%s
metrics: 
%s
%s
%s

%s
%s
</pre><br>
""" % (result[0], splitline, \
       ssplitline, metrics, ssplitline, \
       result[2].reports(verbose=True, score_type=analyst.score_type),
       splitline)

            analyst.analysis_log.write(html)
        else:
            html = """\
<br><p style="font-weight: bold">
best of this round: model #%d, %s<br>
selected metric: %s<br></p>
""" % (result[2], result[1], 
       '%s(%s)' % (analyst.metrics[result[0]][1]['name'],
            analyst.metrics[result[0]][0]))

            analyst.analysis_log.write(html)

    def get_analysis_task_info(self, appid):
        analyst = self.get_analyst(appid)
        return analyst.get_task_info()

    def get_imresult_details(self, appid, i):
        analyst = self.get_analyst(appid)
        best_idx, results = analyst.im_result_details[i]
        details = []
        for result in results:
            feat_idxs, test_result = result
            details.append({
                'metrics': feat_idxs,
                'score': test_result.score(analyst.score_type)[1],
                'fail0': test_result.detail[0]['f']['s'],
                'test0': test_result.detail[0]['f']['s'] + \
                    test_result.detail[0]['p'],
                'fail1': test_result.detail[1]['f']['s'],
                'test1': test_result.detail[1]['f']['s'] + \
                    test_result.detail[1]['p']
            })
        return best_idx, details

class AnalystManagerInterface(object):

    def __init__(self, log_dir, analysis_log_dir):
        self.analyst_manager = AnalystManager(log_dir, analysis_log_dir)
        self.analyst_manager.start()

    def get_analysis_progress(self, appid):
        try:
            r = self.analyst_manager.get_analysis_progress(appid)
            return True, r
        except AnalystManagerException, e:
            return False, e.msg

    def get_imresult_details(self, appid, i):
        try:
            r = self.analyst_manager.get_imresult_details(appid, i)
            return True, r
        except Exception, e:
            logger.exception('')
            return False, str(e)

    def enable_analysis(self, appid, config={}):
        try:
            r = self.analyst_manager.enable_analysis(appid, config)
            return True, r
        except Exception, e:
            logger.exception('')
            return False, str(e)

    def disable_analysis(self, appid):
        try:
            self.analyst_manager.disable_analysis(appid)
            return True, "OK"
        except Exception, e:
            logger.exception('')
            return False, str(e)

    def get_analysis_task_info(self, appid):
        try:
            r = self.analyst_manager.get_analysis_task_info(appid)
            return True, r
        except Exception, e:
            logger.exception('')
            return False, str(e)
        
    def start_analysis(self, appid):
        try:
            self.analyst_manager.start_analysis(appid)
            return True, "OK"
        except AnalystManagerException, e:
            return False, e.msg

    def stop_analysis(self, appid):
        try:
            self.analyst_manager.stop_analysis(appid)
            return True, "OK"
        except AnalystManagerException, e:
            return False, e.msg

    def start_evaluation(self, appid):
        try:
            self.analyst_manager.start_evaluation(appid)
            return True, "OK"
        except AnalystException, e:
            return False, e.args[0]

    def get_evaluation_results(self, appid, start_from=0, qsize=0):
        try:
            return True,\
                self.analyst_manager.get_evaluation_results(appid, start_from, qsize)
        except AnalystManagerException, e:
            return False, e.msg

    def stop_evaluation(self, appid):
        try:
            self.analyst_manager.stop_evaluation(appid)
            return True, "OK"
        except AnalystException, e:
            return False, e.args[0]

if __name__ == '__main__':
    addr = ('', 20061)
    log_dir = '/dev/shm/apache_logs'
    analysis_log_dir = '/dev/shm/analysis_logs'
    try:
        server = SimpleXMLRPCServer(addr)
        ami = AnalystManagerInterface(log_dir, analysis_log_dir)
        server.register_instance(ami)
        server.serve_forever()
    except KeyboardInterrupt:
        ami.analyst_manager.stop()
        ami.analyst_manager.join()
    
#    am = AnalystManager(log_dir)
#    am.start()
#    am.enable_analysis('rubis')
#    try:
#        while True:
#            sleep(60)
#    except KeyboardInterrupt:
#        am.stop()
#        am.join()


