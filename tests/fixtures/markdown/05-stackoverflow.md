# Why is conditional processing of a sorted array faster than of an unsorted array?

In this C++ code, sorting the data (_before_ the timed region) makes the primary loop ~6x faster:

```cpp
#include <algorithm>
#include <ctime>
#include <iostream>

int main()
{
    // Generate data
    const unsigned arraySize = 32768;
    int data[arraySize];

    for (unsigned c = 0; c < arraySize; ++c)
        data[c] = std::rand() % 256;

    // !!! With this, the next loop runs faster.
    std::sort(data, data + arraySize);

    // Test
    clock_t start = clock();
    long long sum = 0;
    for (unsigned i = 0; i < 100000; ++i)
    {
        for (unsigned c = 0; c < arraySize; ++c)
        {   // Primary loop.
            if (data[c] >= 128)
                sum += data[c];
        }
    }

    double elapsedTime = static_cast<double>(clock()-start) / CLOCKS_PER_SEC;

    std::cout << elapsedTime << '\n';
    std::cout << "sum = " << sum << '\n';
}
```

- Without std::sort(data, data + arraySize);, the code runs in 11.54 seconds.
- With the sorted data, the code runs in 1.93 seconds.

(Sorting itself takes more time than this one pass over the array, so it's not actually worth doing if we needed to calculate this for an unknown array.)

---

Initially, I thought this might be just a language or compiler anomaly, so I tried Java:

```java
import java.util.Arrays;
import java.util.Random;

public class Main
{
    public static void main(String[] args)
    {
        // Generate data
        int arraySize = 32768;
        int data[] = new int[arraySize];

        Random rnd = new Random(0);
        for (int c = 0; c < arraySize; ++c)
            data[c] = rnd.nextInt() % 256;

        // !!! With this, the next loop runs faster
        Arrays.sort(data);

        // Test
        long start = System.nanoTime();
        long sum = 0;
        for (int i = 0; i < 100000; ++i)
        {
            for (int c = 0; c < arraySize; ++c)
            {   // Primary loop.
                if (data[c] >= 128)
                    sum += data[c];
            }
        }

        System.out.println((System.nanoTime() - start) / 1000000000.0);
        System.out.println("sum = " + sum);
    }
}
```

With a similar but less extreme result.

---

My first thought was that sorting brings the data into the [cache](https://en.wikipedia.org/wiki/CPU_cache), but that's silly because the array was just generated.

- What is going on?
- Why is processing a sorted array faster than processing an unsorted array?

The code is summing up some independent terms, so the order should not matter.

---

## Related / follow-up Q&As with more modern C++ compilers

- Why is processing an unsorted array the same speed as processing a sorted array with modern x86-64 clang? - modern C++ compilers auto-vectorize the loop, especially when SSE4.1 or AVX2 is available. This avoids any data-dependent branching so performance isn't data-dependent.
- gcc optimization flag -O3 makes code slower than -O2 - branchless scalar with cmov can result in a longer dependency chain (especially when GCC chooses poorly), creating a latency bottleneck that makes it slower than branchy asm for the sorted case.
