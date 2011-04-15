/* PlotWrapper: A Class wraps flot api to enable drawing multiple series in 
 * one chart additively.
 *
 * DataSeries: the helper class for PlotWrapper to hold temporary data.
 */


/* Check dependencies.
 */
//var jQuery;
if(!jQuery || typeof jQuery != 'function')
    throw new Error('jquery.js has not been loaded');
if(!defineClass || typeof defineClass != 'function')
    throw new Error('utils.js has not been loaded');


/* Constructor for DataSeries. The argument can either be a string representing
 * the label of series or an object specifies option attributes. 
 * 
 * An example of object argument:
 * { name: 'line1',
 *   series: { label: 'y = x + 1',
 *             color: 'red',
 *             data: [[0,1], [1,2], [2,3]] }}
 */
var DataSeries = function(args) {
    this.name = (typeof(args) == 'string') ? args : args.name;
    //this.maxLength = args.maxLength || 0;
    this.rawSeries = args.series || {};
    if(!this.rawSeries.label) this.rawSeries.label = this.name;
    if(!this.rawSeries.data) this.rawSeries.data = [];
}

DataSeries.prototype.appendData = function(rawdata) {
    this.rawSeries.data = this.rawSeries.data.concat(rawdata);
}


/* Constructor for PlotWrapper.
 *
 * An example of object argument:
 * { placeholder: 'placeholder',
 *   data: [ds1, new DataSource('line2')],
 *   onDataSeriesUpdate: function(event) {} }
 */
var PlotWrapper = function(args){
    this.canvas = (typeof(args) == 'string') ? jQuery('#' + args): 
        ((typeof(args.placeholder) == 'string') ? jQuery('#' + args.placeholder) :
         args.placeholder);
    this.data = {};
    this.rawSeries = [];
    this.options = args.options || {};
    if(args.onDataSeriesUpdate && 
            typeof args.onDataSeriesUpdate == 'function') {
        jQuery.bind('dataSeriesUpdate', args.onDataSeriesUpdate(dataSeries));
    }
    if(args.data) {
        if(jQuery.isArray(args.data)){
            var dataSeriesList = args.data;
            for(var i = 0; i < dataSeriesList.length; i++) {
                this.addDataSeries(dataSeriesList[i]);
            }
        } else {
            var dataSeries = args.data;
            this.addDataSeries(dataSeries);
        }
    }
}

PlotWrapper.prototype.addDataSeries = function(dataSeries) {
    this.data[dataSeries.name] = dataSeries;
    this.rawSeries.push(dataSeries.rawSeries);
    jQuery(this).trigger('dataSeriesUpdate', [dataSeries]);
}

PlotWrapper.prototype.updateDataSeries = function(dataSeriesName, rawdata) {
    this.data[dataSeriesName].appendData(rawdata);
    jQuery(this).trigger('dataSeriesUpdate', [this.data[dataSeriesName]]);
}

PlotWrapper.prototype.setOptions = function(options) {
    jQuery.extend(this.options, options);
}
    
PlotWrapper.prototype.doPlot = function () {
    jQuery.plot(this.canvas, this.rawSeries, this.options);
}


/*
 * AutoUpdatePlot -- fix length, auto update, etc.
 */
var AutoUpdatePlot = defineClass({
    borrows: PlotWrapper,
    construct: function(args) {
        this.maxLength = args.maxLength || 0;
        jQuery(this).bind('dataSeriesUpdate', function(e, dataSeries) {
            var rawdata = dataSeries.rawSeries.data;
            var len = rawdata.length;
            if(len) {
                var first = rawdata[0][0];
                if(!this.min || this.min > first) {
                    this.min = first;
                }
                var last = rawdata[len - 1][0];
                if(!this.max || this.max < last) {
                    this.max = last;
                }
                //console.log('max: ' + this.max);
                if(this.maxLength > 0) {
                    if(this.max - this.min > this.maxLength ) {
                        this.min = this.max - this.maxLength;
                        this.setOptions({ xaxis: { min: this.min }});
                    }
                }
                //console.log('min: ' + this.min);
            }
        });
        PlotWrapper.call(this, args);
    },
    methods: {
        setAutoUpdate: function(dataSeries, period, updateFunc, args) {
            if(typeof dataSeries == 'string') 
                dataSeries = this.data[dataSeries];
            dataSeries.autoUpdate = true;
            return function() {
                if(dataSeries.autoUpdate) {
                    updateFunc(args);
                    //this.updateDataSeries(dataSeries, updateFunc(args));
                    dataSeries.autoUpdateId = setTimeout(arguments.callee, period);
                }
            };                    
        },
        clearAutoUpdata: function(dataSeries) {
            if(typeof dataSeries == 'string') 
                dataSeries = this.data[dataSeries];
            dataSeries.autoUpdate = false;
            timeoutId = dataSeries.autoUpdateId;
            console.log(timeoutId);
            if(typeof timeoutId == 'number') 
                clearTimeout(timeoutId);
        }
    },
});


/** 
 * PerformancePlot -- time series, auto update thru ajax
 */
var PerformancePlot = defineClass({
    borrows: AutoUpdatePlot,
    construct: function(args) {
    }        
});

