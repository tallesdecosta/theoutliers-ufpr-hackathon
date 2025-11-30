import duckdb
con = duckdb.connect("C:/Users/gabri/Documents/theoutliers-ufpr-hackathon/app/hackathon.duckdb")

# 1. Quais são os tipos na fAvaliacao?
print(con.sql("SELECT DISTINCT TipoPergunta FROM fAvaliacao").df())

# 2. Quais são os tipos na dTipoPergunta?
print(con.sql("SELECT * FROM dTipoPergunta").df())

con.close()
