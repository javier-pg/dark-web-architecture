from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, TimestampType

spark = SparkSession.builder.getOrCreate()

def load_config(spark_context):
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.access.key', MINIO_ACCESS_KEY)
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.secret.key', MINIO_SECRET_KEY)
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.path.style.access', 'true')
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem')
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.endpoint', MINIO_API_ENDPOINT)
    spark_context._jsc.hadoopConfiguration().set('fs.s3a.connection.ssl.enabled', 'false')

load_config(spark.sparkContext)
df = spark.read.json('s3a://onions/sample3.json')
average = df.agg({'amount': 'avg'})
average.show()
