from mcp4xx1 import MCP4xx1


mcp = MCP4xx1(0,16,17)
mcp.wiper1 = 32
mcp.wiper0 = 64
print(mcp.wiper1)
print(mcp.wiper0)
print(bin(mcp.status))