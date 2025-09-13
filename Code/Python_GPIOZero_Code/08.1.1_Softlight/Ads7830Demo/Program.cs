using System;
using System.Device.I2c;
using System.Threading;

namespace Ads7830Demo
{
    public static class Program
    {
        public static void Main()
        {
            // I2C bus 1 на Raspberry Pi, адрес ADS7830 (A0 -> GND)
            const int busId = 1;
            const int address = 0x48;

            using var adc = new Ads7830(busId, address, vref: 3.3);

            // Пример: читаем все 8 каналов раз в секунду
            while (true)
            {
                for (int ch = 0; ch < 8; ch++)
                {
                    byte raw = adc.ReadChannel(ch);
                    double volts = adc.ToVoltage(raw);
                    Console.Write($"CH{ch}: {raw:D3} ({volts:F3} V)  ");
                }
                Console.WriteLine();
                Thread.Sleep(1000);
            }
        }
    }

    /// <summary>
    /// Минималистичный драйвер ADS7830 (8-битный, I2C).
    /// Поддерживает одиночные (single-ended) каналы CH0..CH7.
    /// </summary>
    public sealed class Ads7830 : IDisposable
    {
        private readonly I2cDevice _dev;
        private readonly double _vref;

        // Команды для одиночных каналов (Single-Ended), согласно даташиту.
        // Паттерн управления: 1 0 0 SGL/DIFF ODD/SIGN  SEL1 SEL0 PD1 PD0
        // Здесь подобраны стандартные значения команд под single-ended CH0..CH7.
        private static readonly byte[] CmdCh = new byte[]
        {
            0x84, // CH0
            0xC4, // CH1
            0x94, // CH2
            0xD4, // CH3
            0xA4, // CH4
            0xE4, // CH5
            0xB4, // CH6
            0xF4  // CH7
        };

        public Ads7830(int busId, int address = 0x48, double vref = 3.3)
        {
            _vref = vref;
            var settings = new I2cConnectionSettings(busId, address);
            _dev = I2cDevice.Create(settings);
        }

        /// <summary>
        /// Читает «сырой» 8-битный код с выбранного канала (0..7).
        /// </summary>
        public byte ReadChannel(int channel)
        {
            if (channel < 0 || channel > 7) throw new ArgumentOutOfRangeException(nameof(channel));

            // Пишем команду выбора канала
            _dev.WriteByte(CmdCh[channel]);

            // ADS7830 после переключения канала иногда требует «фиктивное» чтение
            // для обновления результата. Практически помогает короткая задержка
            // или двойное чтение. Оставим простой вариант: короткая пауза + чтение.
            Thread.Sleep(2);

            Span<byte> buf = stackalloc byte[1];
            _dev.Read(buf);
            byte value = buf[0];

            return value;
        }

        /// <summary>
        /// Переводит 8-битный код в напряжение относительно Vref.
        /// </summary>
        public double ToVoltage(byte raw) => raw * _vref / 255.0;

        public void Dispose() => _dev?.Dispose();
    }
}
