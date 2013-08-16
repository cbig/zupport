
def get_tools():
    import inspect
    import tools
    return ([(name, data) for name, data in 
                                inspect.getmembers(tools, inspect.ismodule)])