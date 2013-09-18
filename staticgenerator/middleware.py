import re
from django.conf import settings
from django.utils.importlib import import_module
from staticgenerator import StaticGenerator

class StaticGeneratorMiddleware(object):
    """
    This requires settings.STATIC_GENERATOR_URLS tuple to match on URLs.
    This fork uses the requests incoming host header to allow multiple site
    static generation.
    
    Example::
        
        STATIC_GENERATOR_URLS = (
            r'^/$',
            r'^/blog',
        )
        
    """
    urls = tuple([re.compile(url) for url in settings.STATIC_GENERATOR_URLS])
    gen = StaticGenerator()
    
    def should_generate(self, request, response):
        """
        Hook that allows us to decide if a static response should be generated on a per-request basis.
        """
        processor_path = getattr(settings, 'STATIC_GENERATOR_REQUEST_PROCESSOR', None)
        
        # If a request processor wasn't specifed, default to True (yes, generate static).
        if processor_path is None:
            return True
            
        # Attempt to import and cache the module function.
        if not getattr(self, '_processor', False):
            mod_name, func_name = settings.STATIC_GENERATOR_REQUEST_PROCESSOR.rsplit('.', 1)
            self._processor = getattr(import_module(mod_name), func_name)
        return self._processor(request, response)


    def process_response(self, request, response):
        if response.status_code == 200 and self.should_generate(request, response):
            for url in self.urls:
                if url.match(request.path_info):
                    self.gen.publish_from_path('%s%s'%(request.get_host(), request.path), response.content)
                    break
        return response
