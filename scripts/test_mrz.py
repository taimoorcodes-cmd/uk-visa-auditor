from mrz.checker.td3 import TD3CodeChecker

mrz_code = """P<PAKKHAN<<ALI<AHMED<<<<<<<<<<<<<<<<<<<<<<<<
AA12345678PAK0205154M3001012<<<<<<<<<<<<<<0"""

checker = TD3CodeChecker(mrz_code)
print("Methods available:")
print([m for m in dir(checker) if not m.startswith("_")])