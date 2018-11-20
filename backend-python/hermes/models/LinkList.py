#!/usr/bin/env python
# encoding: utf-8


class DoublyLinkedList(object):
    class Node(object):
        def __init__(self, data=None):
            self.data = data
            self.pre = None
            self.next = None

    def __init__(self):
        head = DoublyLinkedList.Node()
        tail = DoublyLinkedList.Node()
        self.head = head
        self.tail = tail
        self.head.next = self.tail
        self.tail.pre = self.head
        self.size = 0

    def append(self, data):
        node = DoublyLinkedList.Node(data)
        pre = self.tail.pre
        pre.next = node
        node.pre = pre
        self.tail.pre = node
        node.next = self.tail
        self.size += 1
        return node

    def push(self, data):
        return self.insert(0, data)

    def insert(self, index, data):
        index = int(index)
        if index > self.size:
            raise Exception('index out of bounds,list size:%d  get a index:%d' % (self.size, index))

        index = index if index >= 0 else index + 1 + self.size
        next_node = self.get(index)
        if next_node:
            node = DoublyLinkedList.Node(data)
            self.size += 1
            pre_node = next_node.pre
            pre_node.next = node
            node.pre = pre_node
            node.next = next_node
            next_node.pre = node
            return node
        raise Exception('can not find node ,system error')

    def pop(self):
        return self.delete_at(0)

    def delete_at(self, index):
        index = int(index)
        node = self.get(index)
        if node:
            self.__detach__(node)
            return node.data

    def __detach__(self, node):
        node.pre.next = node.next
        node.next.pre = node.pre
        self.size -= 1

    def remove(self, data):
        node = self.head.next
        while node:
            if node.data == data:
                self.__detach__(node)
                return True
            node = node.next
        return False

    def __reversed__(self):
        pre_head = self.head
        tail = self.tail

        def reverse(pre_node, node):
            if node:
                next_node = node.next
                node.next = pre_node
                pre_node.pre = node
                if pre_node is self.head:
                    pre_node.next = None
                if node is self.tail:
                    node.pre = None
                return reverse(node, next_node)
            else:
                self.head = tail
                self.tail = pre_head

        return reverse(self.head, self.head.next)

    def __len__(self):
        return self.size

    def get(self, index):
        index = int(index)
        index = index if index >= 0 else self.size + index
        if index >= self.size or index < 0:
            return None
        node = self.head.next
        while index:
            node = node.next
            index -= 1
        return node

    def set(self, index, data):
        node = self.get(index)
        if node:
            node.data = data
        return node

    def clear(self):
        self.head.next = self.tail
        self.tail.pre = self.head
        self.size = 0

    def travel(self, callback):
        node = self.head.next
        while node is not self.tail:
            callback(node.data)
            node = node.next

    def show(self, order=1):
        if order >= 0:
            node = self.head.next
            while node is not self.tail:
                print(node.data)
                node = node.next
        else:
            node = self.tail.pre
            while node is not self.head:
                print(node.data)
                node = node.pre


# test code
if __name__ == '__main__':
    ls = DoublyLinkedList()
    print "len(ls) %d" % len(ls)
    ls.append(1)
    ls.append(2)
    ls.append(3)
    ls.append(4)
    ls.show(1)
    print "len(ls) %d" % len(ls)
    print "index 0:%d" % ls.get(0).data
    print 'set index(0) = 10'
    ls.set(0, 10)
    ls.show()
    print 'insert index(1) = -2'
    ls.insert(1, -2)
    ls.show()
    print 'delete index(-2)'
    ls.delete_at(-2)
    ls.show()
    print 'reversed'
    reversed(ls)
    ls.show()
    print 'clear:'
    ls.clear()
    ls.show()
