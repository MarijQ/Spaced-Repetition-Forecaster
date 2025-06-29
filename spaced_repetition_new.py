import matplotlib.pyplot as plt

log = []
DAYS = 10000

R = 1
E = 2.5
S = 1
t = 0
t_tot = 0
R0 = 0.9
R_prev = 1
rev_count = 0

# G_L = [3 for i in range(10)]
R_L = [0.9 for i in range(8)]

G_L = [3, 3, 3, 2, 2, 2, 2, 2]
# R_L = [0.9, 0.85, 0.6, 0.9, 0.9, 0.95, 0.5, 0.9, 0.95, 0.95]

while t_tot < DAYS:
    if len(G_L) == 0 or len(R_L) == 0:
        break

    R = round((1 + t / (9 * S)) ** -1 + R_prev - 1, 3)
    # review
    if R <= R_L[0]:
        R_old = R
        S_old = S
        t_old = t
        G = G_L[0]

        R = max(0, R)
        M = min(1.0, (1 - R) / (1 - R0))
        S_A = max(S, t / 9 * ((1 / (R0 - R_prev + 1)) - 1) ** -1)

        M = round(M, 3)
        S_A = round(S_A, 3)

        match G:
            case 0:  # Forgot
                R = R / 2
                E = max(1.3, E - 0.2 * M)
                S = max(1, (1 - M) * S + 0.1 * M * S)
            case 1:  # Hard
                R = (1 + R) / 2
                E = max(1.3, E - 0.15 * M)
                S = (1 - M) * S + M * (0.75 * S + 0.25 * S_A)
            case 2:  # Incidental
                R = (1 + R) / 2
            case 3:  # Good
                R = 1
                S = (1 - M) * S + M * E * (0.5 * S + 0.5 * S_A)
            case 4:  # Easy
                R = 1
                E = max(1.3, E + 0.15 * M)
                S = (1 - M) * S + M * 1.3 * E * S_A

        S = round(S, 3)
        R = round(R, 3)
        E = round(E, 3)

        R_prev = R
        t = 0
        R_L.pop(0)
        G_L.pop(0)
        rev_count += 1
        S_inc = round(S / S_old,3)

        print(f"{rev_count = } \t {t_old = :3} \t {R_old = } \t {G = } \t {R = :5} \t {S = :6} \t {S_inc = }")

    log.append([t_tot, R, E, S])
    t += 1
    t_tot += 1
    # print(f"{t_tot = } \t {R = } \t {E = } \t {S = }")

# graphs
t1 = [x[0] for x in log]
R1 = [x[1] for x in log]
E1 = [x[2] for x in log]
S1 = [x[3] for x in log]

plt.figure(figsize=(7, 10))

ax1 = plt.subplot(311)
ax1.plot(t1, R1, 'r', label="Recall")
ax1.set_xlim(0, t_tot)
ax1.set_ylim(0, 1)
ax1.legend()

ax2 = plt.subplot(312)
ax2.plot(t1, E1, 'g', label="Ease")
ax2.set_xlim(0, t_tot)
ax2.legend()

ax3 = plt.subplot(313)
ax3.plot(t1, S1, 'b', label="Stability")
ax3.set_xlim(0, t_tot)
ax3.legend()

plt.show()
