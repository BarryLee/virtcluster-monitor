import pdb
import logging
import time
from itertools import izip
import copy

import numpy as np

from pebl.data import Dataset, Variable, DiscreteVariable
from pebl.cpd_cont import MultivariateCPD, StatsConcrete
#from pebl.learner.wrapper import WrapperClassifierLearner
from pebl.learner.wrapper_cont import WrapperClassifierLearner
#from pebl.learner.tan_classifier2 import TANClassifierLearner
from pebl.learner.tan_classifier_cont import TANClassifierLearner
#from pebl.learner.nb_classifier import NBClassifierLearner
from pebl.learner.nb_classifier_cont import NBClassifierLearner
from pebl.classifier import Classifier

from monserver.utils.utils import threadinglize
from monserver.api.mon import get_metric_list, get_stats
from monserver.RRD.RRDHandler import RRDHandlerException

import webapi
import cloud

logger = logging.getLogger('analysis.mon_analyst')

#def dummy_observations(num_attrs):
    #return np.zeros((1, num_attrs))

excluded_metrics = [
    #'cpu_nice',
    #'cpu_usage',
    #'dom0_cpu_usage',
    'cpu_idle',
    'dom0_cpu_idle',
    'mem_total',
    'mem_used',
    #'mem_usage',
    'mem_available',
    'swap_total',
    'dom0_swap_total',
    #'packets_in',
    #'packets_out',
    'avgqu_sz',
    'rsecps',
    'wsecps'
]

def check(stats):
    coe_threshold = 1e-05
    var_threshold = 0.01
    
    should_discard = []
    #need_adjust = []

    num_cls, num_attrs = stats.cov.shape[0:2]
    
    cls_list = range(num_cls)
    attr_list = range(num_attrs)
    #[i for i in range(len(cov_qi)) for cov_qi in stats.cov if cov_qi[i, i] == 0]
    should_discard = \
        list(set([i for j in cls_list 
                        for i in attr_list 
                            if stats.coe[j,i,i] == 0 or \
                               abs(stats.cov[j,i,i])/abs(stats.coe[j,i,i]) <= var_threshold]))
#    for j, cov_j in enumerate(stats.cov):
#        for i in attr_list:
#            # check if variance is too small
#            #if cov_j[i,i] - 0 <= var_threshold:
#            if abs(cov_j[i,i])/abs(stats.coe[j,i,i]) <= var_threshold:
#                if i in should_discard:
#                    continue
#                else:
#                    should_discard.append(i)
                    #for tmp_j in cls_list[:j] + cls_list[j+1:]:
                    #    if not cov[tmp_j, i, i] -0 <= var_threshold:
                    #        should_discard.pop()
                    #        need_adjust.append([j,i])
                    #        break
    
    for j in cls_list:
        for xi in attr_list:
            for xj in attr_list:
                if xi == xj: continue
                if xi in should_discard or xj in should_discard: continue
                if abs(stats.cov[j,xi,xj]**2 / (stats.cov[j,xi,xi] * stats.cov[j,xj,xj]) - 1) <= coe_threshold:
                    should_discard.append(xi)

    print stats.variables[[should_discard]]
    #attr_list = [i for i in attr_list if i not in should_discard]

    return should_discard

class AnalystException(Exception):
    pass

class AnalystState(object):
    stopped = 'stopped'
    preparing = 'preparing'
    running = 'running'
    finishing = 'finishing'
    maintain = 'maintain'
    evaluating = 'evaluating'
    error = 'error'

class Analyst(object):
    
    def __init__(self, appid, config={}):
        self.appid = appid
        logger.debug('given config: %s' % config)

        self.buf = []
        self.log_RT_buf = []
        self.obs_buf = []
        self.running = False
        self.state = AnalystState.stopped
        self._first_in_buf = 0

        self._buf_interval = 60
        self._RT_sample_interval = 15

        self._RT_threshold = float(config.get('RT_threshold', 1e5))
        self.batch_update_size = config.get('batch_update_size', 100)
        self.time_to_expire = config.get('time_to_expire', 20*24*3600)
        self.min_obs_size = config.get('min_obs_size', 30)
        self.RT_pct_threshold = config.get('RT_pct_threshold', 0.01)
        self._time_to_flush = config.get('time_to_flush', 5)
        self.include_pm = config.get('include_pm', 0)
        self.excluded_metrics = excluded_metrics.extend(config.get('excluded_metrics', []))

        # config for learner
        self.classifier_type = config.get('classifier_type', 'TAN')
        self.max_num_attr = int(config.get('max_num_attr', 0))
        self.score_good_enough = float(config.get('score_good_enough', 1))
        self.score_type = config.get('score_type', 'BA')
        self.stop_no_better = config.get('stop_no_better', True)
        
        # for debugging
        self.mute = config.get('mute', True)
        self.verbose = config.get('verbose', False)

        self.prepare()

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def get_task_info(self):
        info = {}
        info['RT_threshold'] = self._RT_threshold
        info['metrics'] = self.metrics
        return info

    def prepare(self):
        # get app info (machine list, etc)
        components = self._get_app_comps()

        self.metrics = []
        pms = set()
        self.target = None

        for c in components:
            vmid = c[0]
            vm_metrics = self._get_metrics(vmid)
            for m in vm_metrics:
                self.metrics.append((vmid, m))
            if self.include_pm:
                pmid = c[1]
                pms.add(pmid)
            if c[-1] == 1:
                self.target = c[0]

        if self.include_pm:
            for pmid in pms:
                pm_metrics = self._get_metrics(pmid)
                for m in pm_metrics:
                    self.metrics.append((pmid, m))
                
        self.num_metrics = len(self.metrics)
        #obs = self._collect_data() or dummy_observations(len(self.metrics) + 1)
        self.perf_data_buf = [[] for i in range(self.num_metrics)]

        variables = [Variable('_'.join([host, metric['name']])) for (host, metric) in self.metrics]
        variables.append(DiscreteVariable('cls', 2))
        logger.debug('has %d variables' % len(variables))

        self.variables = np.array(variables)
        self.num_obs = [0] * self.variables[-1].arity
        #pdb.set_trace()
        #self.data = data.Dataset(obs, None, None, variables, None)
        #self.data.check_arities()

    def _get_app_comps(self):
        ret = []
        comps = webapi.queryVm(self.appid)
        if comps is None:
            raise AnalystException, 'no such app: %s' % self.appid
        slaves = comps['slave']
        if len(slaves) > 1:
            raise AnalystException, '%s:donnot auto scale!' % self.appid
        target_id, target_ip = str(slaves[0][0]), slaves[0][1]
        rc, target_info = cloud.get_vm_info(target_id)
        if not rc:
            pmid = pmip = None
        else:
            pmid = pmip = target_info['host']

        dbid = 'db.hustcloud.com'
        dbpmid = 'crane04'
        
        ret.append([target_id, pmid, 1])
        ret.append([dbid, dbpmid, 0])
        return ret

    def _get_metrics(self, vmid):
        rc, metric_grps = get_metric_list(vmid)
        if not rc:
            raise AnalystException, 'cannot get metric list of %s' % vmid
        mlist = []
        processed = set()
        for grp, grpmetrics in metric_grps.items():
            for m in grpmetrics:
                m = copy.deepcopy(m)
                mname = m['name'].split('-')[-1]
                if m['enabled'] and \
                        mname not in self.excluded_metrics and\
                        mname not in processed:
                    #mlist.append(m['name'])
                    processed.add(mname)
                    del m['enabled']
                    if m.has_key('unit') and m['unit'] is None: del m['unit']
                    m['name'] = mname
                    mlist.append(m)

        #logger.debug(mlist)
        return mlist

    def update(self, log_data):
        if self.get_state() == AnalystState.preparing:
            self._update_preparing(log_data)
        elif self.get_state() == AnalystState.running:
            self._update_running(log_data)
        elif self.get_state() == AnalystState.maintain:
            #self._update_maintain(log_data)
            self._update_running(log_data)
        elif self.get_state() == AnalystState.evaluating:
            self._update_evaluating(log_data)

    def _update_common(self, log_data):
        #logger.debug('update()')
        #logger.debug('size of log_data: %d' % len(log_data))
        buf_interval = self._buf_interval

        #log_data = (l.strip().split(None, 2) for l in log_data.splitlines() if l)
        log_data = (l.strip().split(None, 2) for l in log_data)

        if self._first_in_buf:
            base = self._first_in_buf 
        else:
            first_record = log_data.next()
            base = int(first_record[1])
            self._first_in_buf = base
            self.buf.append(first_record)

        now = time.time()
        for rec in log_data:
            t = int(rec[1])
            if now - t > self.time_to_expire:
                continue
            # when the time range of log records in buf exceeds
            # buf_interval, call _aggregate()
            if t - base > buf_interval:
                #logger.debug('size of self.buf b4 call _aggregate(): %d' % len(self.buf))
                #self._aggregate(lambda x: sum(x)/(len(x)+1.0))
                self._aggregate()
                self.buf.append(rec)
                base = t
                self._first_in_buf = base
            else:
                self.buf.append(rec)
        #logger.debug('delta in buf: %d' % (int(self.buf[-1][1]) - int(self.buf[0][1])))

        #logger.debug('buf size: %d, log_RT_buf size: %d' % (len(self.buf), len(self.log_RT_buf)))
        if not len(self.log_RT_buf) > self.batch_update_size:
            return
        st = time.time() * 1000
        obs = self._collect_data()
        logger.debug('used %s milliseconds' % (time.time() * 1000 - st))
        #logger.debug(obs)
        return obs

    def _update_preparing(self, log_data):
        obs = self._update_common(log_data)
        if obs is None:
            return

        self.obs_buf += obs
        logger.debug('# of obs: %d' % len(self.obs_buf))
        logger.debug('# of 1s: %d' % len([i for i in self.obs_buf if i[-1]==1]))

    def _update_running(self, log_data):
        self._update_preparing(log_data)

    def _update_maintain(self, log_data):
        obs = self._update_common(log_data)
        if obs is None:
            return

        obs = np.array(obs)[:, np.append(self.attrs_selected, self.variables.size-1)]
        self.selected_learner.updateCpd(obs)

    def _update_evaluating(self, log_data):
        obs = self._update_common(log_data)
        if obs is None:
            return

        obs = np.array(obs)[:, np.append(self.attrs_selected, self.variables.size-1)]
        self.selected_learner.updateCpd(obs)
        self.evaluate_and_save(obs)

    def to_class(self, time_list):
        total_cnt = len(time_list)
        if not total_cnt > 0:
            return 0
        
        out_thresh_cnt = 0
        for t in time_list:
            if t >= self._RT_threshold:
                out_thresh_cnt += 1
        
        #logger.debug(total_cnt)
        if float(out_thresh_cnt) / total_cnt >= self.RT_pct_threshold or \
           out_thresh_cnt >= self._RT_sample_interval:
        #    logger.debug('%d/%d' % (out_thresh_cnt, total_cnt))
        #    if out_thresh_cnt >= self._RT_sample_interval:
            return 1
        return 0
        
    def _aggregate(self):
        # process data in buf, do actual updating on cpd
        #logger.debug('_aggregate()')
        #logger.debug(self.buf[0][1])
        if len(self.buf) == 0:
            return
        self.buf.sort()

        sbuf = []
        base = self._first_in_buf
        RT_sample_interval = self._RT_sample_interval

        #logger.debug('delta in buf: %d' % (int(self.buf[-1][1]) - int(self.buf[0][1])))
        for (c, t, r) in iter(self.buf):
            others, RT = r.rsplit(None, 1)
            t = int(t)
            RT = int(RT)
            # put data spans a RT_sample_interval into sbuf, then 
            # aggregate the data, convert to one class
            if t - base > RT_sample_interval:
                self.log_RT_buf.append((base, self.to_class(sbuf)))
                sbuf = [RT]
                base = t
            else:
                sbuf.append(RT)
        # clear buffer
        #self.buf = []
        del self.buf[:]

        if len(self.log_RT_buf) == 0:
            self.log_RT_buf.append((base, self.to_class(sbuf)))

    def ready4analysis(self):
        # count obs of each class
        for c in self.num_obs:
            if c < self.min_obs_size:
                return False

        return True
    
    def do_analysis(self):
        if not hasattr(self, 'learner'):
            obs = np.array(self.obs_buf)
            del self.obs_buf[:]
            data = Dataset(obs, None, None, self.variables, None)
            data.check_arities()
            # TODO select learner class
            learner_config = {
                'score_good_enough': self.score_good_enough,
                'max_num_attr': self.max_num_attr,
            }
            if self.classifier_type == 'NB':
                self.learner = WrapperClassifierLearner(NBClassifierLearner, data, **learner_config)
            else:
                self.learner = WrapperClassifierLearner(TANClassifierLearner, data, **learner_config)
        #elif len(self.obs_buf):
            #obs = np.array(self.obs_buf)
            #del self.obs_buf[:]
            #self.learner.addObs(obs)
        else:
            raise AnalystException, 'a learner is already learned!'
        self.preprocess()
        return self.learner.run(
                        mute=self.mute, 
                        verbose=self.verbose, 
                        score_type=self.score_type,
                        stop_no_better=self.stop_no_better
                        )

    def stop_analysis(self):
        if hasattr(self, 'learner'):
            self.learner.stop()

    def _collect_data(self):
        logger.debug('_collect_data()')
        obs = []

        # convert response times to 0/1s
        #RT_clses = [(i[0], 0 if i[1] < self._RT_threshold else 1) 
        #        for i in self.log_RT_buf]
        RT_clses = self.log_RT_buf

        step = self._RT_sample_interval
        start = RT_clses[0][0]
        end = RT_clses[-1][0]
        stop = False

        st = time.time() * 1000
        #j = 0
        for metric_buf, (hid, metric) in izip(self.perf_data_buf, self.metrics):
            metric = metric['name']
            try:
                rdata = get_stats(hid, metric, step=step, startTime=start, endTime=end)[1]
                rsz = len(rdata)
                i = 0
                if len(metric_buf):
                    while i < rsz and rdata[i][0] <= metric_buf[-1][0]:
                        i += 1
                #else:
                    #j += 1
                    #print j
                #logger.debug('i=%d' % i)
                metric_buf += rdata[i:]
            except RRDHandlerException, e:
                logger.exception('data is not ready')
                stop = True
                break
        # end for
        if stop:
            logger.debug('collect no data')
            return None

        logger.debug('used %s milliseconds to get_stats' % (time.time() * 1000 - st))

        st = time.time() * 1000
        last_processed = 0
        for (t, v) in RT_clses:
            ob = []
            discard = False
            for metric_buf, (hid, metric) in izip(self.perf_data_buf, self.metrics):
                #closest = bin_search_closest([r[0] for r in metric_buf], t)
                if len(metric_buf) == 0:
                    logger.warning("data is not ready")
                    stop = True
                    break
                metric = metric['name']
                closest = bin_search_closest(metric_buf, t)
                tt, vv = metric_buf[closest]
                if vv is None:
                    logger.warning("None data: %s at %s, rt is %s" %
                           (metric, t, v))
                    discard = True
                    break
                if abs(t - tt) > step:
                    if closest == 0 and t < tt:
                        logger.warning("no data is so old as %s" % t)
                    elif closest == len(metric_buf) - 1 and t > tt: 
                        logger.warning("data is not ready")
                        stop = True
                        break
                    else:
                        logger.warning("offset too large: %s" % 
                                (abs(tt - t),))
                        logger.debug("closest index is %d" % closest)
                    discard = True
                    break

                ob.append(vv)
            # end for
            if stop:
                break
            last_processed += 1
            if discard:
                continue
            ob.append(v)
            obs.append(ob)
            self.num_obs[v] += 1
        # end for
        logger.debug('used %s milliseconds to forge obs' % (time.time() * 1000 - st))

        st = time.time() * 1000
        # clear self.perf_data_buf
        for metric_buf in self.perf_data_buf:
            del metric_buf[:]

        # reserve records from last_processed
        del self.log_RT_buf[:last_processed]
        #logger.debug(self.log_RT_buf)
        #self.last = last
        #logger.debug(obs)
        logger.debug('used %s milliseconds to do other stuff' % (time.time() * 1000 - st))
        if len(obs):
            #logger.debug(i)
            #return np.array(obs)
            return obs
        else:
            logger.debug('collect no data')
            return None

    def preprocess(self):
        prohibited_attrs = check(self.learner.stats)
        self.learner.set_prohibited_attrs(prohibited_attrs)
        return prohibited_attrs
        
    def finish_analysis(self):
        self.selected_learner = self.learner.getSelectedLearner()
        self.attrs_selected = sorted(self.learner.attrs_selected)
        self.classifier = Classifier(self.selected_learner)
        self.set_state(AnalystState.maintain)

    def start_post_evaluation(self):
        if self.get_state() == AnalystState.evaluating:
            return
        if self.get_state() != AnalystState.maintain:
            raise AnalystException, 'learning is not finished'
        if not hasattr(self, 'evaluation_results'):
            self.evaluation_results = { 'tc': 0, 'fc': 0, 'results': [] }
        self.set_state(AnalystState.evaluating)
        self.config_batch_size = self.batch_update_size
        self.batch_update_size = 1
        if len(self.obs_buf):
            try:
                obs = np.array(self.obs_buf)[:, np.append(self.attrs_selected, self.variables.size-1)] 
            except Exception, e:
                pdb.set_trace() 
                obs = None
            del self.obs_buf[:]
            self.evaluate_and_save(obs)

    def evaluate_and_save(self, obs):
        #obs = np.array(obs)[self.attrs_selected]
        for ob in obs:
            logger.debug('%d, %d' % (self.classifier.classify(ob[:-1]), ob[-1]))
            ans = self.classifier.classify(ob[:-1])
            self.evaluation_results['tc'] += 1
            if ans != ob[-1]:
                self.evaluation_results['fc'] += 1
            ob_ans = np.append(ob, ans).tolist()
            self.evaluation_results['results'].append(ob_ans)
        # end for

    def stop_post_evaluation(self):
        if self.get_state() != AnalystState.evaluating:
            raise AnalystException, 'evaluation is not running'
        self.set_state(AnalystState.maintain)
        self.batch_update_size = self.config_batch_size

    def get_feature_val(self, metric_idx):
        assert metric_idx != self.learner.num_attr
        #pdb.set_trace()
        #cpd = self.learner._cpd_cache.get((metric_idx, self.learner.num_attr))
        #e0 = cpd.coe[0][0][0]**.5
        #s0 = cpd.cov[0][0][0]**.5
        #e1 = cpd.coe[1][0][0]**.5
        #s1 = cpd.cov[1][0][0]**.5
        e0 = self.learner.stats.condExp(metric_idx, 0)
        e1 = self.learner.stats.condExp(metric_idx, 1)
        s0 = self.learner.stats.condVariance(metric_idx, 0)**.5
        s1 = self.learner.stats.condVariance(metric_idx, 1)**.5
        logger.debug('%s:\ne0=%s,s0=%s\ne1=%s,s1=%s' % (self.metrics[metric_idx], e0, s0, e1, s1))
        return float((e0+e1+(s0-s1 if e1 > e0 else s1-s0)) / 2.0)

def bin_search_closest(lst, k):
    last = len(lst) - 1
    l, u = 0, last

    m = (l + u)/2
    while l <= u:
        if k == lst[m][0]:
        #if k == lst[m]:
            return m
        elif k > lst[m][0]:
        #elif k > lst[m]:
            l = m + 1
        else:
            u = m - 1 
        m = (l + u)/2

    if u < 0:
        return 0
    if l > last:
        return last
    if k - lst[u][0] > lst[l][0] - k:
    #if k - lst[u] > lst[l] - k:
        return l
    else:
        return u

