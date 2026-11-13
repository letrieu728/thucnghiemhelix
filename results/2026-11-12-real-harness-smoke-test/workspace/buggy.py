def sum_first_n(n):
    """Return 1 + 2 + ... + n."""
    total = 0
    for i in range(n):
        total += i
    return total


if __name__ == "__main__":
    print(sum_first_n(5))
