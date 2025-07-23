"""
异步迭代工具模块

该模块提供了处理异步生成器的工具函数，特别是将一个异步生成器分流为多个独立流，
以便在不同的异步任务中重用相同的数据流。

作者: 光明实验室媒体智能团队
"""

import asyncio


async def atee(async_generator):
    """
    将一个异步生成器分流成两个独立的异步生成器
    
    类似于Unix系统中的tee命令，将一个数据流分成两个相同的流，
    以便不同的消费者可以同时处理相同的数据流而不相互影响。
    
    Args:
        async_generator: 源异步生成器
        
    Returns:
        tuple: 包含两个异步生成器和一个任务对象的元组
            - 第一个异步生成器，会产生与源生成器相同的数据
            - 第二个异步生成器，会产生与源生成器相同的数据
            - 负责填充队列的异步任务，可用于监控或取消操作
    """
    queue1 = asyncio.Queue()
    queue2 = asyncio.Queue()

    async def populate_queues():
        """
        从源生成器读取数据并填充两个队列
        
        当源生成器结束时，向两个队列发送None以表示结束
        """
        async for item in async_generator:
            await queue1.put(item)
            await queue2.put(item)

    task = asyncio.create_task(populate_queues())

    async def get_from_queue(queue):
        """
        从队列中读取数据并产生为异步生成器
        
        Args:
            queue: 要读取的asyncio队列
            
        Yields:
            从队列中获取的数据项，直到遇到None
        """
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

    return get_from_queue(queue1), get_from_queue(queue2), task
