import nidaqmx


def processing(ui, gui):
    sample_counter = 0
    raw_data_buffer = []
    notch_buffer = []
    a = 0.88
    N = 5
    first_lpf_buffer = []
    first_comb_filter_buffer = []
    second_comb_filter_buffer = []
    smoothing_filter_buffer = []
    previous_sample_after_second_lpf = 0
    p1_lst = []
    p2_lst = []
    qrs_lst = []
    qrs_candidates = []
    current_qrs_value = 0
    detection_treshold = 0.0000016
    after_second_lpf_sample = 0
    heart_rate_counter = 1
    heart_rate_period_sum = 0
    with nidaqmx.Task() as task, open(ui.filepath, "w") as f:
        task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
        task.timing.cfg_samp_clk_timing(250)
        while True:
            actual_sample = task.read()
            f.write(str(actual_sample) + "\n")
            if sample_counter < 25:
                raw_data_buffer.append(actual_sample)
                notch_buffer.append(actual_sample)
                first_lpf_buffer.append(actual_sample)
                first_comb_filter_buffer.append(actual_sample)
                second_comb_filter_buffer.append(actual_sample)
                smoothing_filter_buffer.append(actual_sample)
                sample_counter += 1
                continue
            if sample_counter == 25:
                raw_data_buffer = raw_data_buffer[20:]
                notch_buffer = notch_buffer[20:]
                first_lpf_buffer = first_lpf_buffer[15:]
                second_comb_filter_buffer = second_comb_filter_buffer[18:]
                smoothing_filter_buffer = smoothing_filter_buffer[14:]
            after_notch_sample = actual_sample - raw_data_buffer[0] + a * notch_buffer[0]
            raw_data_buffer.append(actual_sample)
            raw_data_buffer.pop(0)
            notch_buffer.append(after_notch_sample)
            notch_buffer.pop(0)
            after_first_lpf_sample = 0.125 * (notch_buffer[4] +
                                              2 * notch_buffer[3] + 2 * notch_buffer[2] +
                                              2 * notch_buffer[1] + notch_buffer[0])
            first_lpf_buffer.append(after_first_lpf_sample)
            first_lpf_buffer.pop(0)
            after_first_comb_filter_sample = 0.25 * (first_lpf_buffer[9]
                                                     - 2 * first_lpf_buffer[5] + first_lpf_buffer[0])
            first_comb_filter_buffer.append(after_first_comb_filter_sample)
            first_comb_filter_buffer.pop(0)
            after_second_comb_filter_sample = 0.25 * abs(first_comb_filter_buffer[24]
                                                         - first_comb_filter_buffer[16] +
                                                         first_comb_filter_buffer[8]
                                                         - first_comb_filter_buffer[0])
            second_comb_filter_buffer.append(after_second_comb_filter_sample)
            second_comb_filter_buffer.pop(0)
            after_smoothing_filter_sample = (second_comb_filter_buffer[6] +
                                             second_comb_filter_buffer[5] + second_comb_filter_buffer[4] +
                                             second_comb_filter_buffer[2] + second_comb_filter_buffer[1] +
                                             second_comb_filter_buffer[0]) / 6
            smoothing_filter_buffer.append(after_smoothing_filter_sample)
            smoothing_filter_buffer.pop(0)
            for i in range(len(smoothing_filter_buffer)):
                after_second_lpf_sample += smoothing_filter_buffer[i] ** 2
            after_second_lpf_sample = after_second_lpf_sample / N
            if sample_counter > 250:
                if after_second_lpf_sample > detection_treshold and previous_sample_after_second_lpf < detection_treshold:
                    p1_lst.append(sample_counter)
                if len(p1_lst) > len(p2_lst):
                    qrs_candidates.append((after_second_lpf_sample, sample_counter))
                if after_second_lpf_sample < detection_treshold and previous_sample_after_second_lpf > detection_treshold:
                    if len(p1_lst) > 0:
                        p2_lst.append(sample_counter)
                        qrs_lst.append((p2_lst[-1] + p1_lst[-1]) // 2)
                        if len(qrs_lst) >= 2:
                            if ui.period == 0:
                                large_boxes = (qrs_lst[-1] - qrs_lst[-2]) / 50
                                heart_rate_period_sum += 300 // large_boxes
                                ui.heart_rate = round(heart_rate_period_sum / heart_rate_counter, 2)
                                heart_rate_counter += 1
                                ui.set_text_label()
                            else:
                                large_boxes = (qrs_lst[-1] - qrs_lst[-2]) / 50
                                heart_rate_period_sum += 300 // large_boxes
                                ui.heart_rate = round(heart_rate_period_sum / heart_rate_counter, 2)
                                ui.set_text_label()
                                if heart_rate_counter == ui.period:
                                    heart_rate_period_sum = 0
                                    heart_rate_counter = 0
                                heart_rate_counter += 1
                if len(p2_lst) >= 1 and sample_counter == (10 + p2_lst[-1]):
                    previous_detection_treshold = detection_treshold
                    for qrs in qrs_candidates:
                        if qrs[1] == qrs_lst[-1]:
                            current_qrs_value = qrs[0]
                            qrs_candidates = []
                    detection_treshold = 0.25 * (previous_detection_treshold + 1.5 * current_qrs_value)
            previous_sample_after_second_lpf = after_second_lpf_sample
            after_second_lpf_sample = 0

            if len(p1_lst) > 10:
                p1_lst.pop(0)
            if len(p2_lst) > 10:
                p2_lst.pop(0)
            if len(qrs_lst) > 10:
                qrs_lst.pop(0)
            sample_counter += 1

            if ui.stop_program_flag:
                break
            if gui.stop_data:
                break

            if ui.stop_program_flag or gui.stop_data:
                break
