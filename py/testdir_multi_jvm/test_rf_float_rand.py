import os, json, unittest, time, shutil, sys
sys.path.extend(['.','..','py'])

import h2o, h2o_cmd
import h2o_browse as h2b
import random

print "ASSUMING max FP single precision (hex rep. 7f7f ffff) approx. 3.4028234 * 10**38"

def write_syn_dataset(csvPathname, rowCount, headerData):
    dsf = open(csvPathname, "w+")
    
    # output is just 0 or 1 randomly
    dsf.write(headerData + "\n")
    # add random output. just 0 or 1
    for i in range(rowCount):
        rowData = rand_rowData()
        dsf.write(rowData + "," + str(random.randint(0,1)) + "\n")
    dsf.close()

# append!
def append_syn_dataset(csvPathname, num):
    with open(csvPathname, "a") as dsf:
        for i in range(num):
            rowData = rand_rowData()
            dsf.write(rowData + "\n")


def rand_rowData():
    # UPDATE: maybe because of byte buffer boundary issues, single byte
    # data is best? if we put all 0s or 1, then I guess it will be bits?
    rowData = str(random.uniform(0,7))
    for i in range(7):
        # h2o used to only support single (HEX-638)
        # rowData = rowData + "," + str(random.uniform(-1e30,1e30))
        rowData = rowData + "," + str(random.uniform(-1e59,1e59))
    return rowData

class parse_rand_schmoo(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global SEED, localhost
        SEED = h2o.setup_random_seed()
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(2,java_heap_MB=1300,use_flatfile=True)
        else:
            import h2o_hosts
            h2o_hosts.build_cloud_with_hosts()

    @classmethod
    def tearDownClass(cls):
        if not h2o.browse_disable:
            # time.sleep(500000)
            pass

        h2o.tear_down_cloud(h2o.nodes)
    
    def test_rf_float_rand(self):
        SYNDATASETS_DIR = h2o.make_syn_dir()
        csvFilename = "syn_prostate.csv"
        csvPathname = SYNDATASETS_DIR + '/' + csvFilename

        headerData = "ID,CAPSULE,AGE,RACE,DPROS,DCAPS,PSA,VOL,GLEASON"

        totalRows = 1000
        write_syn_dataset(csvPathname, totalRows, headerData)


        for trial in range (5):
            rowData = rand_rowData()
            num = random.randint(4096, 10096)
            append_syn_dataset(csvPathname, num)
            totalRows += num
            start = time.time()

            # make sure all key names are unique, when we re-put and re-parse (h2o caching issues)
            key = csvFilename + "_" + str(trial)
            key2 = csvFilename + "_" + str(trial) + ".hex"
            # On EC2 once we get to 30 trials or so, do we see polling hang? GC or spill of heap or ??
            kwargs = {'ntree': 5, 'depth': 5}
            key = h2o_cmd.runRF(csvPathname=csvPathname, key=key, key2=key2, 
                timeoutSecs=15, pollTimeoutSecs=5, **kwargs)
            print "trial #", trial, "totalRows:", totalRows, "num:", num, "RF end on ", csvFilename, \
                'took', time.time() - start, 'seconds'
            ### h2o_cmd.runInspect(key=key2)
            ### h2b.browseJsonHistoryAsUrlLastMatch("Inspect")
            h2o.check_sandbox_for_errors()


if __name__ == '__main__':
    h2o.unit_main()
