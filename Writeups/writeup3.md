1. Examine create_bacteria_db.sh, how many tables will be created in the database?
3 databases

2. In the insert_gff_table.py script you submitted, explain the logic of using try and except. Why is this necessary?
To avoid competition among tasks which try to write into the single bacteria.db file simultaneously.

Query the Created Database
Runtime changes between nonindxing and indexing
    1. Non-indexing
Total number of record ids:  4100
Processed 0 record ids in 3.9769248962402344 seconds
Processed 10 record ids in 15.008628606796265 seconds
Processed 20 record ids in 26.00050163269043 seconds
Processed 30 record ids in 36.97225785255432 seconds
        
    2. Indexing
Apptainer> time python query_bacteria_db.py --database_path bacteria.db
Total number of record ids:  4100
Processed 0 record ids in 0.5448338985443115 seconds
Processed 10 record ids in 0.5689589977264404 seconds
Processed 20 record ids in 0.5784273147583008 seconds
Processed 30 record ids in 0.6096653938293457 seconds

The dramatic is due to database indexing.
Without an Index, the database must perform a Full Table Scan for every single query.

With an Index, the database creates and uses a sorted index. When you query for a record, it performs an Index Seek. 
This eliminates the need to scan the entire dataset for each lookup, making the process faster.


Explain the role of CHUNK_SIZE and why it is necessary
The role of CHUNK_SIZE is to signify the number of rows of data read into a memory at once.
This is necessary because if the dataset is huge, if one wants to read all the data at one, the memory will not be enough and the program will crash.

Explain why the following chunk configuration makes sense - what kind of data access pattern is expected, and why does this align with biological use cases?
chunk_size = 1000
chunks = (chunk_size, n_features)
The expected data access pattern is to retrieve all of the features of a given row (protein).
This alignes with biological use cases because in biology, we don't usually want one feature of all the rows
but instead we more frequently want to have access to all the features per sample. 

