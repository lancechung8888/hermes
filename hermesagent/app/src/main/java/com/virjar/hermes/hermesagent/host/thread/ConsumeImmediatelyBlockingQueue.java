package com.virjar.hermes.hermesagent.host.thread;

import android.support.annotation.NonNull;

import java.util.Collection;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;

/**
 * Created by virjar on 2018/2/25.<br>
 * 对队列包装增强,当任务被投递的时候,先看一级线程池是否空闲,如果空闲直接往一级线程池投递,同时吞掉该任务
 */
public class ConsumeImmediatelyBlockingQueue<T> implements BlockingQueue<T> {
    private BlockingQueue<T> delegate;
    private ImmediatelyConsumer<T> immediatelyConsumer;

    public interface ImmediatelyConsumer<T> {
        boolean consume(T t);
    }

    ConsumeImmediatelyBlockingQueue(BlockingQueue<T> delegate, ImmediatelyConsumer<T> immediatelyConsumer) {
        this.delegate = delegate;
        this.immediatelyConsumer = immediatelyConsumer;
    }

    @Override
    public boolean add(T t) {
        return immediatelyConsumer.consume(t) || delegate.add(t);
    }

    @Override
    public boolean offer(@NonNull T t) {
        return immediatelyConsumer.consume(t) || delegate.offer(t);
    }

    @Override
    public T remove() {
        return delegate.remove();
    }

    @Override
    public T poll() {
        return delegate.poll();
    }

    @Override
    public T element() {
        return delegate.element();
    }

    @Override
    public T peek() {
        return delegate.peek();
    }

    @Override
    public void put(T t) throws InterruptedException {
        if (immediatelyConsumer.consume(t)) {
            return;
        }
        delegate.put(t);
    }


    @Override
    public boolean offer(T t, long timeout, @NonNull TimeUnit unit) throws InterruptedException {
        return immediatelyConsumer.consume(t) || delegate.offer(t, timeout, unit);
    }

    @Override
    public T take() throws InterruptedException {
        return delegate.take();
    }

    @Override
    public T poll(long timeout, @NonNull TimeUnit unit) throws InterruptedException {
        return delegate.poll(timeout, unit);
    }

    @Override
    public int remainingCapacity() {
        return delegate.remainingCapacity();
    }

    @Override
    public boolean remove(Object o) {
        return delegate.remove(o);
    }

    @Override
    public boolean containsAll(@NonNull Collection<?> c) {
        return delegate.containsAll(c);
    }


    @Override
    public boolean addAll(@NonNull Collection<? extends T> c) {
        List<T> remain = new LinkedList<>();
        for (T t : c) {
            if (!immediatelyConsumer.consume(t)) {
                remain.add(t);
            }
        }
        return delegate.addAll(remain);
    }

    @Override
    public boolean removeAll(@NonNull Collection<?> c) {
        return delegate.removeAll(c);
    }

    @Override
    public boolean retainAll(@NonNull Collection<?> c) {
        return delegate.retainAll(c);
    }

    @Override
    public void clear() {
        delegate.clear();
    }

    @Override
    public int size() {
        return delegate.size();
    }

    @Override
    public boolean isEmpty() {
        return delegate.isEmpty();
    }

    @Override
    public boolean contains(Object o) {
        return delegate.contains(o);
    }


    @NonNull
    @Override
    public Iterator<T> iterator() {
        return delegate.iterator();
    }

    @NonNull
    @Override
    public Object[] toArray() {
        return delegate.toArray();
    }

    @NonNull
    @Override
    public <T1> T1[] toArray(@NonNull T1[] a) {
        return delegate.toArray(a);
    }

    @Override
    public int drainTo(@NonNull Collection<? super T> c) {
        return delegate.drainTo(c);
    }

    @Override
    public int drainTo(@NonNull Collection<? super T> c, int maxElements) {
        return delegate.drainTo(c, maxElements);
    }
}
