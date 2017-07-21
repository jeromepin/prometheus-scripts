#!/usr/bin/env python3

import abc
import time

import prometheus_client as prometheus

class PrometheusAbstractCollector(object, metaclass=abc.ABCMeta):
    def __init__(self, **kwargs):
        print(1)
        self.setup(**kwargs)
        print(2)

    def register(self, metric):
        self.metrics[metric.name] = metric

    def listen(self, port):
        prometheus.start_http_server(port)

    def collect(self):
        for name, metric in self.metrics.items():
            yield metric

class PrometheusAsyncCollector(PrometheusAbstractCollector):
    _methods = []

    def setup(self, **kwargs):
        self.metrics = {}
        self.delay   = kwargs.get('delay')

        self.listen(kwargs.get('port'))
        prometheus.REGISTRY.register(self)

        self.retrieve_metrics()

    def run(func):
        PrometheusAsyncCollector._methods.append(func)
        return func

    def retrieve_metrics(self):
        while True:
            for method in PrometheusAsyncCollector._methods:
                method(self)

            time.sleep(self.delay)

class PrometheusSyncCollector(PrometheusAbstractCollector):
    _methods = []

    def setup(self, **kwargs):
        self.metrics = {}
        self.listen(kwargs.get('port'))
        prometheus.REGISTRY.register(self)

        while True:
            time.sleep(2)

    def run(func):
        PrometheusSyncCollector._methods.append(func)
        return func

    def retrieve_metrics(self):
        for method in self.__class__.__bases__[0]._methods:
            method(self)

    def collect(self):
        self.retrieve_metrics()

        for name, metric in self.metrics.items():
            yield metric
