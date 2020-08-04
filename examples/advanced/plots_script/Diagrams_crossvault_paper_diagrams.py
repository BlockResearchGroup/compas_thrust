import os
from compas_tno.plotters import open_csv
from compas_tno.plotters import interpolate_min_thk
from compas_tno.plotters import open_csv_row
from compas_tno.plotters import diagram_of_multiple_thrust
import matplotlib.pyplot as plt
from numpy import array

# ['o', '^', 's', 'D', 'x', '1', '2', '3', 'v', 'p', '4', '8']


def GSF_plot(Parameters, GSF, legends, markers, colors, save=None):

    fig = plt.figure(figsize=[8, 6])
    ax = fig.add_subplot()

    for i in range(len(Parameters)):
        print(Parameters[i])
        print(GSF[i])
        ax.plot(Parameters[i], GSF[i], markers[i], ls='-', color=colors[i], label=legends[i])

    ax.set_xlabel('Radius', weight='bold')
    ax.set_ylabel('GSF', weight='bold')
    ax.legend()
    if save:
        plt.savefig(save)
    plt.show()

    return


xs = []
mins = []
maxs = []
legends = []
colors = []

thk = 0.6
span = 10.0
type_structures = ['pointed_crossvault']
type_formdiagrams = ['cross_fd', 'fan_fd']
hcs = [5.00, 5.48, 5.92, 6.32, 6.71, 7.07, 7.42, 7.75, 8.06, 8.37, 8.66] # [5.00, 5.92, 6.71, 7.42, 8.06, 8.66, 9.22, 9.75]
Rs = [5, 6, 7, 8, 9, 10, 11, 12]
colors_list = ['#D2B4DE', '#b4c0de']
discretisation = 10
markers = ['o', '^', 's', 'D', 'x', '1', '2', '3']*10
xy_limits = [[0.60, 0.20], [110, 30]]
legend = False

GSF = []
RS = []
GSF_Legends = []

for type_structure in type_structures:
    for type_formdiagram in type_formdiagrams:
        R = 5
        gsf_pattern = []
        rs_pattern = []
        for hc in hcs:
            folder = os.path.join('/Users/mricardo/compas_dev/me', 'shape_comparison', type_structure, type_formdiagram, 'h='+str(hc))
            title = type_structure + '_' + type_formdiagram + '_discr_' + str(discretisation)
            csv_file = os.path.join(folder, title + '_data.csv')
            print(csv_file)
            sizes, solutions = open_csv_row(csv_file)
            size_parameters = sizes[0]
            solutions_min = solutions[0]
            solutions_max = solutions[1]
            xs.append(size_parameters)
            mins.append(solutions_min)
            maxs.append(solutions_max)
            min_thk = interpolate_min_thk(size_parameters, solutions_min, solutions_max)
            gsf_pattern.append(thk/min_thk)
            rs_pattern.append(R)
            if type_formdiagram == type_formdiagrams[0]:
                colors.append(colors_list[0])
            else:
                colors.append(colors_list[1])
            legends.append('Crossvault R='+str(R)+'_'+type_formdiagram)
            R += 0.5
        GSF.append(gsf_pattern)
        RS.append(rs_pattern)
        GSF_Legends.append(type_formdiagram)

print('Check on the parameters size')
print(len(xs))
print(len(mins))
print(len(maxs))
print(len(colors))
print(len(legends))

print(GSF)
print(RS)
GSF_file = os.path.join('/Users/mricardo/compas_dev/me', 'shape_comparison', type_structure, 'GSF_plot.pdf')
GSF_plot(RS, GSF, GSF_Legends, markers, colors_list, save=GSF_file)

# diagram_file = os.path.join('/Users/mricardo/compas_dev/me', 'shape_comparison', type_structure, 'diagram_GSF_cross_fd.pdf')
# diagram_of_multiple_thrust(xs, mins, maxs, legends, colors=colors, save=diagram_file, fill=True, show_legend=legend, xy_limits=xy_limits, markers=markers).show()
